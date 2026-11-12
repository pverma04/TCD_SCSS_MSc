import Foundation
import SQLite3

struct Recording: Identifiable {
    let id: String
    let started: Date
    let ended: Date?
    let count: Int
}

final class Database {
    private var db: OpaquePointer?
    private let transient = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

    init(storeURL: URL? = nil) throws {
        let url: URL
        if let storeURL { url = storeURL }
        else {
            let folder = try FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
            url = folder.appendingPathComponent("motion.sqlite")
        }
        guard sqlite3_open(url.path, &db) == SQLITE_OK else {
            throw NSError(domain: "SQLite", code: 1, userInfo: [NSLocalizedDescriptionKey: "Cannot open the recording database."])
        }
        try execute("PRAGMA foreign_keys = ON")
        try execute("PRAGMA journal_mode = WAL")
        try execute("CREATE TABLE IF NOT EXISTS recordings (id TEXT PRIMARY KEY, started REAL NOT NULL, ended REAL)")
        try execute("CREATE TABLE IF NOT EXISTS samples (recording_id TEXT NOT NULL REFERENCES recordings(id), timestamp REAL NOT NULL, uptime REAL NOT NULL, x REAL NOT NULL, y REAL NOT NULL, z REAL NOT NULL)")
        try execute("CREATE INDEX IF NOT EXISTS samples_recording ON samples(recording_id)")
        // A previous process may have been terminated during capture.
        try execute("UPDATE recordings SET ended = COALESCE((SELECT MAX(timestamp) FROM samples WHERE recording_id = recordings.id), started) WHERE ended IS NULL")
    }

    deinit { sqlite3_close(db) }

    private func failure() -> Error {
        NSError(domain: "SQLite", code: Int(sqlite3_errcode(db)), userInfo: [NSLocalizedDescriptionKey: String(cString: sqlite3_errmsg(db))])
    }

    private func execute(_ sql: String) throws {
        guard sqlite3_exec(db, sql, nil, nil, nil) == SQLITE_OK else { throw failure() }
    }

    private func statement(_ sql: String) throws -> OpaquePointer {
        var result: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &result, nil) == SQLITE_OK, let result = result else { throw failure() }
        return result
    }

    private func bind(_ text: String, to statement: OpaquePointer, at index: Int32) {
        _ = text.withCString { sqlite3_bind_text(statement, index, $0, -1, transient) }
    }

    private func finish(_ statement: OpaquePointer) throws {
        guard sqlite3_step(statement) == SQLITE_DONE else { throw failure() }
    }

    func start(id: String, date: Date) throws {
        let s = try statement("INSERT INTO recordings (id, started) VALUES (?, ?)")
        defer { sqlite3_finalize(s) }
        bind(id, to: s, at: 1)
        sqlite3_bind_double(s, 2, date.timeIntervalSince1970)
        try finish(s)
    }

    func append(id: String, timestamp: Double, uptime: Double, x: Double, y: Double, z: Double) throws {
        let s = try statement("INSERT INTO samples VALUES (?, ?, ?, ?, ?, ?)")
        defer { sqlite3_finalize(s) }
        bind(id, to: s, at: 1)
        for (offset, value) in [timestamp, uptime, x, y, z].enumerated() {
            sqlite3_bind_double(s, Int32(offset + 2), value)
        }
        try finish(s)
    }

    func end(id: String) throws {
        let s = try statement("UPDATE recordings SET ended = ? WHERE id = ?")
        defer { sqlite3_finalize(s) }
        sqlite3_bind_double(s, 1, Date().timeIntervalSince1970)
        bind(id, to: s, at: 2)
        try finish(s)
    }

    func recordings() throws -> [Recording] {
        let s = try statement("SELECT r.id, r.started, r.ended, COUNT(s.rowid) FROM recordings r LEFT JOIN samples s ON s.recording_id = r.id GROUP BY r.id ORDER BY r.started DESC")
        defer { sqlite3_finalize(s) }
        var result: [Recording] = []
        var status = sqlite3_step(s)
        while status == SQLITE_ROW {
            result.append(Recording(id: String(cString: sqlite3_column_text(s, 0)), started: Date(timeIntervalSince1970: sqlite3_column_double(s, 1)), ended: sqlite3_column_type(s, 2) == SQLITE_NULL ? nil : Date(timeIntervalSince1970: sqlite3_column_double(s, 2)), count: Int(sqlite3_column_int64(s, 3))))
            status = sqlite3_step(s)
        }
        guard status == SQLITE_DONE else { throw failure() }
        return result
    }

    func export(_ recording: Recording) throws -> URL {
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent("Exports", isDirectory: true)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let url = folder.appendingPathComponent("accelerometer-\(recording.id).csv")
        try Data("session_id,timestamp_utc,unix_seconds,sensor_uptime_seconds,x_g,y_g,z_g\n".utf8).write(to: url, options: .atomic)
        let file = try FileHandle(forWritingTo: url)
        defer { try? file.close() }
        try file.seekToEnd()
        let s = try statement("SELECT timestamp, uptime, x, y, z FROM samples WHERE recording_id = ? ORDER BY uptime")
        defer { sqlite3_finalize(s) }
        bind(recording.id, to: s, at: 1)
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        var status = sqlite3_step(s)
        while status == SQLITE_ROW {
            let values = (0..<5).map { sqlite3_column_double(s, Int32($0)) }
            let line = "\(recording.id),\(formatter.string(from: Date(timeIntervalSince1970: values[0])))," + values.map { String($0) }.joined(separator: ",") + "\n"
            try file.write(contentsOf: Data(line.utf8))
            status = sqlite3_step(s)
        }
        guard status == SQLITE_DONE else { throw failure() }
        return url
    }
}

extension Database {
    func prepareCommutes() throws {
        try execute("CREATE TABLE IF NOT EXISTS journeys (id TEXT PRIMARY KEY, route TEXT NOT NULL, started REAL NOT NULL, ended REAL, completed INTEGER NOT NULL DEFAULT 0, distance REAL NOT NULL DEFAULT 0, location_count INTEGER NOT NULL DEFAULT 0)")
        try execute("CREATE TABLE IF NOT EXISTS upload_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL, payload BLOB NOT NULL)")
        try execute("CREATE TABLE IF NOT EXISTS journey_chunks (journey_id TEXT NOT NULL, chunk_id TEXT NOT NULL, payload BLOB NOT NULL, PRIMARY KEY(journey_id, chunk_id))")
        // Interrupted journeys are never included in arrival estimates.
        let interrupted = try journeys().filter { $0.ended == nil }
        for j in interrupted {
            try updateJourney(id: j.id, ended: Date().timeIntervalSince1970, completed: false, distance: j.distance, locations: j.locationCount)
        }
    }

    func startJourney(id: String, route: String, started: Double) throws {
        let s = try statement("INSERT INTO journeys (id, route, started) VALUES (?, ?, ?)")
        defer { sqlite3_finalize(s) }
        bind(id, to: s, at: 1); bind(route, to: s, at: 2)
        sqlite3_bind_double(s, 3, started)
        try finish(s)
        try queueMetadata(id: id)
    }

    func updateJourney(id: String, ended: Double?, completed: Bool, distance: Double, locations: Int) throws {
        let s = try statement("UPDATE journeys SET ended = ?, completed = ?, distance = ?, location_count = ? WHERE id = ?")
        defer { sqlite3_finalize(s) }
        if let ended { sqlite3_bind_double(s, 1, ended) } else { sqlite3_bind_null(s, 1) }
        sqlite3_bind_int(s, 2, completed ? 1 : 0)
        sqlite3_bind_double(s, 3, distance)
        sqlite3_bind_int64(s, 4, Int64(locations))
        bind(id, to: s, at: 5)
        try finish(s)
        try queueMetadata(id: id)
    }

    private func queueMetadata(id: String) throws {
        guard let j = try journeys().first(where: { $0.id == id }) else { return }
        var object: [String: Any] = ["route": j.route, "startedAt": j.started * 1000, "completed": j.completed, "distanceMeters": j.distance, "locationCount": j.locationCount, "station": "dublin-airport", "schemaVersion": 1]
        object["endedAt"] = j.ended.map { $0 * 1000 as Any } ?? NSNull()
        object["uploadedAt"] = [".sv": "timestamp"]
        try enqueue(path: "journeys/\(id)/metadata", payload: JSONSerialization.data(withJSONObject: object))
    }

    func saveChunk(journeyID: String, chunk: UploadChunk) throws {
        let id = UUID().uuidString
        let payload = try JSONEncoder().encode(chunk)
        try execute("BEGIN IMMEDIATE")
        do {
            let s = try statement("INSERT INTO journey_chunks VALUES (?, ?, ?)")
            defer { sqlite3_finalize(s) }
            bind(journeyID, to: s, at: 1); bind(id, to: s, at: 2)
            _ = payload.withUnsafeBytes { sqlite3_bind_blob(s, 3, $0.baseAddress, Int32(payload.count), transient) }
            try finish(s)
            var json = try JSONSerialization.jsonObject(with: payload) as! [String: Any]
            json["uploadedAt"] = [".sv": "timestamp"]
            try enqueue(path: "journeys/\(journeyID)/chunks/\(id)", payload: JSONSerialization.data(withJSONObject: json))
            try execute("COMMIT")
        } catch { try? execute("ROLLBACK"); throw error }
    }

    private func enqueue(path: String, payload: Data) throws {
        let s = try statement("INSERT INTO upload_queue (path, payload) VALUES (?, ?)")
        defer { sqlite3_finalize(s) }
        bind(path, to: s, at: 1)
        _ = payload.withUnsafeBytes { sqlite3_bind_blob(s, 2, $0.baseAddress, Int32(payload.count), transient) }
        try finish(s)
    }

    func pending() throws -> [PendingUpload] {
        let s = try statement("SELECT id, path, payload FROM upload_queue ORDER BY id LIMIT 20")
        defer { sqlite3_finalize(s) }
        var result: [PendingUpload] = []
        var status = sqlite3_step(s)
        while status == SQLITE_ROW {
            result.append(PendingUpload(id: sqlite3_column_int64(s, 0), path: String(cString: sqlite3_column_text(s, 1)), payload: Data(bytes: sqlite3_column_blob(s, 2), count: Int(sqlite3_column_bytes(s, 2)))))
            status = sqlite3_step(s)
        }
        guard status == SQLITE_DONE else { throw failure() }
        return result
    }

    func acknowledge(_ id: Int64) throws {
        let s = try statement("DELETE FROM upload_queue WHERE id = ?")
        defer { sqlite3_finalize(s) }
        sqlite3_bind_int64(s, 1, id); try finish(s)
    }

    func pendingCount() throws -> Int {
        let s = try statement("SELECT COUNT(*) FROM upload_queue")
        defer { sqlite3_finalize(s) }
        guard sqlite3_step(s) == SQLITE_ROW else { throw failure() }
        return Int(sqlite3_column_int64(s, 0))
    }

    func journeys() throws -> [Journey] {
        let s = try statement("SELECT id, route, started, ended, completed, distance, location_count FROM journeys ORDER BY started DESC")
        defer { sqlite3_finalize(s) }
        var rows: [Journey] = []
        var status = sqlite3_step(s)
        while status == SQLITE_ROW {
            rows.append(Journey(id: String(cString: sqlite3_column_text(s, 0)), route: String(cString: sqlite3_column_text(s, 1)), started: sqlite3_column_double(s, 2), ended: sqlite3_column_type(s, 3) == SQLITE_NULL ? nil : sqlite3_column_double(s, 3), completed: sqlite3_column_int(s, 4) == 1, distance: sqlite3_column_double(s, 5), locationCount: Int(sqlite3_column_int64(s, 6))))
            status = sqlite3_step(s)
        }
        guard status == SQLITE_DONE else { throw failure() }
        return rows
    }

    func exportRoute(_ journey: Journey) throws -> URL {
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent("Exports", isDirectory: true)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let url = folder.appendingPathComponent("route-\(journey.id).csv")
        try Data("session_id,unix_seconds,latitude,longitude,accuracy_m,speed_m_s\n".utf8).write(to: url)
        let file = try FileHandle(forWritingTo: url)
        defer { try? file.close() }
        try file.seekToEnd()
        let s = try statement("SELECT payload FROM journey_chunks WHERE journey_id = ? ORDER BY rowid")
        defer { sqlite3_finalize(s) }
        bind(journey.id, to: s, at: 1)
        var status = sqlite3_step(s)
        while status == SQLITE_ROW {
            let data = Data(bytes: sqlite3_column_blob(s, 0), count: Int(sqlite3_column_bytes(s, 0)))
            let chunk = try JSONDecoder().decode(UploadChunk.self, from: data)
            for p in chunk.locations {
                let line = "\(journey.id),\(p.timestamp),\(p.latitude),\(p.longitude),\(p.accuracy),\(p.speed.map { String($0) } ?? "")\n"
                try file.write(contentsOf: Data(line.utf8))
            }
            status = sqlite3_step(s)
        }
        guard status == SQLITE_DONE else { throw failure() }
        return url
    }
}

import Foundation
import CoreLocation

struct Journey: Identifiable {
    let id: String
    let route: String
    let started: Double
    let ended: Double?
    let completed: Bool
    let distance: Double
    let locationCount: Int
}

struct MotionPoint: Codable {
    let timestamp: Double
    let uptime: Double
    let x: Double
    let y: Double
    let z: Double
}

struct RoutePoint: Codable {
    let timestamp: Double
    let latitude: Double
    let longitude: Double
    let accuracy: Double
    let speed: Double?
}

struct UploadChunk: Codable {
    let capturedAt: Double
    let motion: [MotionPoint]
    let locations: [RoutePoint]
}

struct PendingUpload {
    let id: Int64
    let path: String
    let payload: Data
}

// A baseline, not a weather-dependent prediction. Keep direction labels separate.
enum CommuteEstimate {
    static func minutes(route: String, journeys: [Journey]) -> Int? {
        let durations = journeys.filter { $0.route == route && $0.completed && $0.locationCount >= 2 }
            .compactMap { j -> Double? in
                guard let end = j.ended, end > j.started else { return nil }
                return end - j.started
            }.sorted()
        guard durations.count >= 3 else { return nil }
        let mid = durations.count / 2
        let median = durations.count.isMultiple(of: 2) ? (durations[mid - 1] + durations[mid]) / 2 : durations[mid]
        return max(1, Int(ceil(median / 60)))
    }
}

#if canImport(UIKit)
import SwiftUI

@MainActor
final class WalkLocation: NSObject, ObservableObject, CLLocationManagerDelegate {
    @Published var points: [CLLocationCoordinate2D] = []
    @Published var status = "Location permission required"
    var onPoint: ((CLLocation) -> Void)?
    private let manager = CLLocationManager()
    private var active = false

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.distanceFilter = 5
        manager.activityType = .fitness
    }

    var authorized: Bool { [.authorizedWhenInUse, .authorizedAlways].contains(manager.authorizationStatus) }
    func requestPermission() { manager.requestWhenInUseAuthorization() }
    func start() {
        active = true
        points = []
        status = "Waiting for a GPS fix"
        manager.startUpdatingLocation()
    }
    func stop() { active = false; manager.stopUpdatingLocation() }
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        status = authorized ? "Location ready" : "Enable location in Settings to record a route"
    }
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard active else { return }
        for point in locations where point.horizontalAccuracy >= 0 && point.horizontalAccuracy <= 50 && abs(point.timestamp.timeIntervalSinceNow) < 15 {
            points.append(point.coordinate)
            status = "GPS accuracy ±\(Int(point.horizontalAccuracy)) m"
            onPoint?(point)
        }
    }
    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        status = "GPS: \(error.localizedDescription)"
    }
}

#endif

extension Database {
    func bindCloud(uid: String, databaseURL: String) throws {
        try execute("CREATE TABLE IF NOT EXISTS cloud_binding (singleton INTEGER PRIMARY KEY CHECK(singleton = 1), uid TEXT NOT NULL, url TEXT NOT NULL)")
        let check = try statement("SELECT uid, url FROM cloud_binding WHERE singleton = 1")
        defer { sqlite3_finalize(check) }
        let status = sqlite3_step(check)
        if status == SQLITE_ROW {
            let owner = String(cString: sqlite3_column_text(check, 0))
            let url = String(cString: sqlite3_column_text(check, 1))
            guard owner == uid && url == databaseURL else {
                throw NSError(domain: "Cloud ownership", code: 1, userInfo: [NSLocalizedDescriptionKey: "This phone's journey database belongs to a different Firebase account/project. Sign into the original account; data has not been uploaded to the new one."])
            }
        } else {
            guard status == SQLITE_DONE else { throw failure() }
            let s = try statement("INSERT INTO cloud_binding VALUES (1, ?, ?)")
            defer { sqlite3_finalize(s) }
            bind(uid, to: s, at: 1); bind(databaseURL, to: s, at: 2); try finish(s)
        }
    }
}

extension Database {
    func saveWeather(_ observations: [OpenWeatherObservation]) throws -> Int {
        try execute("CREATE TABLE IF NOT EXISTS weather_seen (id TEXT PRIMARY KEY, observed REAL NOT NULL)")
        var added = 0
        for observation in observations {
            let check = try statement("SELECT COUNT(*) FROM weather_seen WHERE id = ?")
            bind(observation.id, to: check, at: 1)
            guard sqlite3_step(check) == SQLITE_ROW else { sqlite3_finalize(check); throw failure() }
            let exists = sqlite3_column_int(check, 0) > 0
            sqlite3_finalize(check)
            if exists { continue }
            try execute("BEGIN IMMEDIATE")
            do {
                try enqueue(path: "weather/dublin-airport/observations/\(observation.id)", payload: observation.payload)
                let s = try statement("INSERT INTO weather_seen VALUES (?, ?)")
                defer { sqlite3_finalize(s) }
                bind(observation.id, to: s, at: 1)
                sqlite3_bind_double(s, 2, observation.snapshot.observedAt)
                try finish(s)
                try execute("COMMIT")
                added += 1
            } catch { try? execute("ROLLBACK"); throw error }
        }
        return added
    }
}
