import SwiftUI
import CoreMotion
import UIKit

@MainActor
final class Recorder: ObservableObject {
    @Published var isRecording = false
    @Published var count = 0
    @Published var x = 0.0
    @Published var y = 0.0
    @Published var z = 0.0
    @Published var recordings: [Recording] = []
    @Published var errorMessage: String?
    @Published var exportURL: URL?
    private let motion = CMMotionManager()
    private var database: Database?
    private var activeID: String?
    private var epochOffset = 0.0

    init() {
        do {
            database = try Database()
            try refresh()
        } catch { errorMessage = error.localizedDescription }
    }

    func start() {
        guard !isRecording else { return }
        guard motion.isAccelerometerAvailable else {
            errorMessage = "Accelerometer unavailable. Run this app on a physical iPhone or iPad; the simulator cannot capture motion."
            return
        }
        guard let database = database else { errorMessage = "Database unavailable. Restart the app and try again."; return }
        do {
            let id = UUID().uuidString
            let now = Date()
            try database.start(id: id, date: now)
            activeID = id
            epochOffset = now.timeIntervalSince1970 - ProcessInfo.processInfo.systemUptime
            count = 0
            exportURL = nil
            isRecording = true
            UIApplication.shared.isIdleTimerDisabled = true
            motion.accelerometerUpdateInterval = 1.0 / 50.0
            motion.startAccelerometerUpdates(to: .main) { [weak self] data, error in
                // Core Motion delivers this handler on the main operation queue.
                MainActor.assumeIsolated {
                    guard let self = self, self.isRecording, self.activeID == id else { return }
                    if let error = error { self.end(); self.errorMessage = error.localizedDescription; return }
                    guard let data = data else { return }
                    do {
                        try database.append(id: id, timestamp: self.epochOffset + data.timestamp, uptime: data.timestamp, x: data.acceleration.x, y: data.acceleration.y, z: data.acceleration.z)
                        self.count += 1
                        self.x = data.acceleration.x
                        self.y = data.acceleration.y
                        self.z = data.acceleration.z
                    } catch {
                        self.end()
                        self.errorMessage = "Capture stopped because a sample could not be saved: \(error.localizedDescription)"
                    }
                }
            }
            try refresh()
        } catch { errorMessage = error.localizedDescription }
    }

    func end() {
        motion.stopAccelerometerUpdates()
        isRecording = false
        UIApplication.shared.isIdleTimerDisabled = false
        guard let id = activeID else { return }
        do {
            try database?.end(id: id)
            activeID = nil
            try refresh()
        } catch { errorMessage = error.localizedDescription }
    }

    func export(_ recording: Recording) {
        do { exportURL = try database?.export(recording) }
        catch { errorMessage = error.localizedDescription }
    }

    private func refresh() throws { recordings = try database?.recordings() ?? [] }
}
