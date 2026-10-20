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

    init() throws {
        let folder = try FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
        guard sqlite3_open(folder.appendingPathComponent("motion.sqlite").path, &db) == SQLITE_OK else {
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
