import Foundation

enum WeatherChecks {
    static func run() throws {
        let now = ISO8601DateFormatter().date(from: "2026-11-05T12:00:00Z")!
        func row(_ fields: [String: Any] = [:]) -> [String: Any] {
            ["name": "Dublin Airport", "date": "05-11-2026", "reportTime": "10:00", "temperature": " 10 ", "rainfall": "0.9", "windSpeed": "19", "weatherDescription": "Rain "].merging(fields) { _, new in new }
        }
        func parse(_ rows: [[String: Any]]) throws -> [OpenWeatherObservation] {
            try OpenWeather.normalize(data: JSONSerialization.data(withJSONObject: rows), fetchedAt: now)
        }
        let sample = try parse([row()])[0]
        precondition(sample.snapshot.observedAt == now.addingTimeInterval(-7200).timeIntervalSince1970 * 1000)
        precondition(sample.snapshot.fetchedAt == now.timeIntervalSince1970 * 1000)
        precondition(sample.snapshot.temperatureC == 10 && sample.snapshot.rainfallMM == 0.9 && sample.snapshot.windSpeedKnots == 19)
        let summer = try parse([row(["date": "01-07-2026"])])[0]
        precondition(summer.snapshot.observedAt == ISO8601DateFormatter().date(from: "2026-07-01T09:00:00Z")!.timeIntervalSince1970 * 1000)
        let missing = try parse([row(["temperature": "-99", "rainfall": NSNull(), "windSpeed": "NA"])])[0]
        precondition(missing.snapshot.temperatureC == nil && missing.snapshot.rainfallMM == nil && missing.snapshot.windSpeedKnots == nil)
        let ordered = try parse([row(["reportTime": "11:00"]), row()])
        precondition(ordered[0].snapshot.observedAt < ordered[1].snapshot.observedAt)
        for invalid in [row(["date": "bad"]), row(["name": "Other"]), row(["date": "06-11-2026"]), row(["date": "25-10-2026", "reportTime": "01:00"]), row(["date": "29-03-2026", "reportTime": "01:00"])] {
            do { _ = try parse([invalid]); fatalError("Invalid or ambiguous weather time accepted") }
            catch { /* expected */ }
        }
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: dir) }
        let url = dir.appendingPathComponent("weather.sqlite")
        var database: Database? = try Database(storeURL: url)
        try database!.prepareCommutes()
        precondition(try! database!.saveWeather(ordered) == 2)
        precondition(try! database!.pendingCount() == 2)
        database = nil
        database = try Database(storeURL: url)
        precondition(try! database!.saveWeather(ordered) == 0)
        precondition(try! database!.pendingCount() == 2)
        let queued = try database!.pending()
        precondition(queued[0].path.contains("weather/dublin-airport/observations/"))
        for config in [CloudConfiguration(databaseURL: "http://evil.example", apiKey: "key", enabled: true), CloudConfiguration(databaseURL: "https://example.firebaseio.com", apiKey: "a&key=b", enabled: true)] {
            do { try config.validate(); fatalError("Unsafe cloud configuration accepted") } catch { /* expected */ }
        }
        print("PASS: weather schema, units, missing data, Dublin timezone/DST, provider order, deduplication across relaunch, cloud URL validation")
    }
}
