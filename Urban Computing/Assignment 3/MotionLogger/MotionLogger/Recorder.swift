import SwiftUI
import CoreMotion
import CoreLocation
import UIKit

@MainActor
final class Recorder: ObservableObject {
    @Published var isRecording = false
    @Published var count = 0
    @Published var x = 0.0
    @Published var y = 0.0
    @Published var z = 0.0
    @Published var recordings: [Recording] = []
    @Published var journeys: [Journey] = []
    @Published var errorMessage: String?
    @Published var exportURL: URL?
    @Published var route = "To college"
    @Published var distance = 0.0
    @Published var locationCount = 0
    @Published var pendingCount = 0
    @Published var cloudStatus = "Cloud not configured"
    @Published var lastUploaded: Date?
    @Published var cloudUID = ""
    @Published var accountBusy = false
    @Published var syncing = false
    @Published var configuration = CloudConfiguration.load()
    @Published var weather: WeatherSnapshot?
    @Published var weatherStatus = "Weather not loaded"
    let location = WalkLocation()
    private let motion = CMMotionManager()
    private let cloud = CloudSync()
    private var database: Database?
    private var activeID: String?
    private var epochOffset = 0.0
    private var lastRecordedUptime: TimeInterval?
    private var motionBuffer: [MotionPoint] = []
    private var locationBuffer: [RoutePoint] = []
    private var previousLocation: CLLocation?
    private var lastGPS: Date?
    private var syncTask: Task<Void, Never>?
    private var flushTimer: Timer?
    private var startedAt: Date?
    private var lastWeatherCheck = Date.distantPast
    private var weatherFetching = false
    private var nextSyncAttempt = Date.distantPast
    private var retryDelay = 2.0

    var estimatedMinutes: Int? { CommuteEstimate.minutes(route: route, journeys: journeys) }

    init() {
        do {
            let db = try Database()
            try db.prepareCommutes()
            database = db
            try refresh()
            if let uid = try cloud.storedUID(config: configuration) {
                try db.bindCloud(uid: uid, databaseURL: configuration.databaseURL)
                cloudUID = uid
                cloudStatus = configuration.enabled ? "Ready to sync" : "Uploads paused"
            }
        } catch { errorMessage = error.localizedDescription }
        location.onPoint = { [weak self] point in self?.receive(point) }
        flushTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.tick() }
        }
    }

    func saveConfiguration(_ draft: CloudConfiguration) {
        guard !isRecording, !syncing, !accountBusy else { return }
        var candidate = draft
        do {
            candidate.databaseURL = candidate.databaseURL.trimmingCharacters(in: .whitespacesAndNewlines).trimmingCharacters(in: CharacterSet(charactersIn: "/"))
            candidate.apiKey = candidate.apiKey.trimmingCharacters(in: .whitespacesAndNewlines)
            if candidate.enabled { try candidate.validate() }
            if !cloudUID.isEmpty { _ = try cloud.storedUID(config: candidate) }
            configuration = candidate
            configuration.save()
            if !configuration.enabled {
                cloudStatus = "Cloud paused · recording stays local"
            } else if cloudUID.isEmpty {
                cloudStatus = "Settings saved · sign in with email/password"
            } else {
                cloudStatus = "Signed in · ready to sync"
                sync(force: true)
                refreshWeather()
            }
        } catch { errorMessage = error.localizedDescription }
    }

    func signIn(email: String, password: String) async {
        guard !accountBusy, !syncing, !isRecording, let database else { return }
        accountBusy = true
        cloudStatus = "Signing in…"
        defer {
            accountBusy = false
            if !cloudUID.isEmpty { sync(force: true); refreshWeather() }
        }
        do {
            let uid = try await cloud.signIn(email: email.trimmingCharacters(in: .whitespacesAndNewlines), password: password, config: configuration)
            do { try database.bindCloud(uid: uid, databaseURL: configuration.databaseURL) }
            catch { try? cloud.signOut(); throw error }
            cloudUID = uid
            cloudStatus = "Signed in · uploads \(configuration.enabled ? "enabled" : "paused")"
        } catch {
            cloudUID = ""
            cloudStatus = "Sign-in failed · check the account settings"
            errorMessage = error.localizedDescription
        }
    }

    func signOut() {
        guard !syncing, !accountBusy, !isRecording else { return }
        do {
            try cloud.signOut(); cloudUID = ""; weather = nil
            cloudStatus = "Signed out · data stays on this phone"
        } catch { errorMessage = error.localizedDescription }
    }

    func resetPassword(email: String) async {
        guard !accountBusy else { return }
        accountBusy = true
        defer { accountBusy = false }
        do { try await cloud.resetPassword(email: email, config: configuration); errorMessage = "If the account exists, check its inbox for password reset instructions." }
        catch { errorMessage = error.localizedDescription }
    }

    func start() {
        guard !isRecording else { return }
        guard activeID == nil else { errorMessage = "Finish saving the previous journey before starting another. Restart if the database remains unavailable."; return }
        guard location.authorized else {
            location.requestPermission()
            errorMessage = "Allow location access, then tap Start again. This app needs GPS to record your commute."
            return
        }
        guard motion.isAccelerometerAvailable else {
            errorMessage = "Use a physical iPhone to collect accelerometer data."
            return
        }
        guard let database else { errorMessage = "Database unavailable. Restart the app."; return }
        do {
            let id = UUID().uuidString, now = Date()
            try database.start(id: id, date: now)
            try database.startJourney(id: id, route: route, started: now.timeIntervalSince1970)
            activeID = id; startedAt = now
            epochOffset = now.timeIntervalSince1970 - ProcessInfo.processInfo.systemUptime
            lastRecordedUptime = nil
            count = 0; distance = 0; locationCount = 0; lastGPS = nil
            motionBuffer = []; locationBuffer = []; previousLocation = nil; exportURL = nil
            isRecording = true
            UIApplication.shared.isIdleTimerDisabled = true
            location.start()
            motion.accelerometerUpdateInterval = 5.0
            motion.startAccelerometerUpdates(to: .main) { [weak self] data, error in
                MainActor.assumeIsolated {
                    guard let self, self.isRecording, self.activeID == id else { return }
                    if let error { self.end(); self.errorMessage = error.localizedDescription; return }
                    guard let data else { return }
                    if let last = self.lastRecordedUptime, data.timestamp - last < 5.0 { return }
                    do {
                        let timestamp = self.epochOffset + data.timestamp
                        try database.append(id: id, timestamp: timestamp, uptime: data.timestamp, x: data.acceleration.x, y: data.acceleration.y, z: data.acceleration.z)
                        self.motionBuffer.append(MotionPoint(timestamp: timestamp, uptime: data.timestamp, x: data.acceleration.x, y: data.acceleration.y, z: data.acceleration.z))
                        self.lastRecordedUptime = data.timestamp
                        self.count += 1; self.x = data.acceleration.x; self.y = data.acceleration.y; self.z = data.acceleration.z
                    } catch {
                        self.end()
                        self.errorMessage = "Capture stopped: \(error.localizedDescription)"
                    }
                }
            }
            try refresh()
            refreshWeather()
        } catch { errorMessage = error.localizedDescription }
    }

    private func receive(_ point: CLLocation) {
        guard isRecording, let startedAt, point.timestamp >= startedAt,
              lastGPS.map({ point.timestamp > $0 }) ?? true else { return }
        if let previousLocation {
            let seconds = point.timestamp.timeIntervalSince(previousLocation.timestamp)
            let meters = point.distance(from: previousLocation)
            // Reject implausible jumps for a walking-only journey, rather than counting them as distance.
            if seconds > 0 && meters / seconds > 5 { return }
            distance += meters
        }
        previousLocation = point; lastGPS = point.timestamp
        locationCount += 1
        locationBuffer.append(RoutePoint(timestamp: point.timestamp.timeIntervalSince1970, latitude: point.coordinate.latitude, longitude: point.coordinate.longitude, accuracy: point.horizontalAccuracy, speed: point.speed >= 0 ? point.speed : nil))
    }

    private func flush() throws {
        guard let database, let id = activeID, !motionBuffer.isEmpty || !locationBuffer.isEmpty else { return }
        try database.saveChunk(journeyID: id, chunk: UploadChunk(capturedAt: Date().timeIntervalSince1970, motion: motionBuffer, locations: locationBuffer))
        motionBuffer.removeAll(keepingCapacity: true); locationBuffer.removeAll(keepingCapacity: true)
        try database.updateJourney(id: id, ended: nil, completed: false, distance: distance, locations: locationCount)
    }

    private func tick() {
        do { if isRecording { try flush() }; pendingCount = try database?.pendingCount() ?? 0 }
        catch { end(); errorMessage = "Local save failed: \(error.localizedDescription)" }
        sync()
        if Date().timeIntervalSince(lastWeatherCheck) >= 60 { refreshWeather() }
    }

    // End without marking arrival when backgrounded, interrupted, or cancelled.
    func end() { finish(completed: false) }
    func arrive() { finish(completed: true) }
    private func finish(completed: Bool) {
        guard isRecording, let id = activeID, let database else { return }
        motion.stopAccelerometerUpdates(); location.stop()
        isRecording = false; UIApplication.shared.isIdleTimerDisabled = false
        do {
            try flush()
            try database.end(id: id)
            try database.updateJourney(id: id, ended: Date().timeIntervalSince1970, completed: completed && locationCount >= 2, distance: distance, locations: locationCount)
            activeID = nil
            try refresh()
            sync()
        } catch { errorMessage = "Journey ended; saving needs attention: \(error.localizedDescription)" }
    }

    func sync(force: Bool = false) {
        if force { nextSyncAttempt = .distantPast }
        guard configuration.enabled else { return }
        guard !cloudUID.isEmpty else {
            if !accountBusy { cloudStatus = "Sign in with email/password to enable uploads" }
            return
        }
        guard Date() >= nextSyncAttempt, !accountBusy, syncTask == nil, let database else { return }
        let config = configuration
        let owner = cloudUID
        syncing = true
        syncTask = Task { [weak self] in
            defer { self?.syncTask = nil; self?.syncing = false }
            do {
                try database.bindCloud(uid: owner, databaseURL: config.databaseURL)
                let rows = try database.pending()
                if rows.isEmpty { self?.cloudStatus = self?.lastUploaded == nil ? "Signed in · no queued data" : "All queued data uploaded"; return }
                self?.cloudStatus = "Uploading…"
                for row in rows {
                    guard let self, self.configuration.enabled else { return }
                    let uid = try await self.cloud.upload(row, config: config, expectedUID: owner)
                    try database.acknowledge(row.id)
                    self.cloudUID = uid
                    self.lastUploaded = Date()
                }
                self?.pendingCount = try database.pendingCount()
                self?.cloudStatus = "Server acknowledged upload"
                self?.retryDelay = 2
            } catch {
                guard let self else { return }
                self.cloudStatus = "Waiting to sync: \(error.localizedDescription)"
                self.nextSyncAttempt = Date().addingTimeInterval(self.retryDelay)
                self.retryDelay = min(60, self.retryDelay * 2)
            }
        }
    }

    func refreshWeather() {
        guard configuration.enabled, !cloudUID.isEmpty, !weatherFetching, let database else { return }
        weatherFetching = true
        lastWeatherCheck = Date()
        Task {
            defer { weatherFetching = false }
            do {
                let observations = try await OpenWeather.collect()
                let added = try database.saveWeather(observations)
                weather = observations.last?.snapshot
                weatherStatus = "Weather checked; \(added) new observation(s) queued"
                pendingCount = try database.pendingCount()
                sync()
            } catch { weatherStatus = "Weather collection failed: \(error.localizedDescription)" }
        }
    }

    func export(_ recording: Recording) {
        do { exportURL = try database?.export(recording) }
        catch { errorMessage = error.localizedDescription }
    }
    func exportRoute(_ journey: Journey) {
        do { exportURL = try database?.exportRoute(journey) }
        catch { errorMessage = error.localizedDescription }
    }
    private func refresh() throws {
        recordings = try database?.recordings() ?? []
        journeys = try database?.journeys() ?? []
        pendingCount = try database?.pendingCount() ?? 0
    }
}
