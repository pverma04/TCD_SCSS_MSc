import Foundation

@main
struct DatabaseChecks {
    static func main() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: dir) }
        let url = dir.appendingPathComponent("test.sqlite")
        var db: Database? = try Database(storeURL: url)
        try db!.prepareCommutes()
        let id = UUID().uuidString
        let start = Date().timeIntervalSince1970 - 600
        try db!.start(id: id, date: Date(timeIntervalSince1970: start))
        try db!.startJourney(id: id, route: "To college", started: start)
        let motion = MotionPoint(timestamp: start + 1, uptime: 123, x: 0, y: 0, z: 1)
        try db!.append(id: id, timestamp: start + 1, uptime: 123, x: 0, y: 0, z: 1)
        let gps = RoutePoint(timestamp: start + 1, latitude: 53.34, longitude: -6.25, accuracy: 5, speed: nil)
        try db!.saveChunk(journeyID: id, chunk: UploadChunk(capturedAt: start + 2, motion: [motion], locations: [gps]))
        let queue = try db!.pending()
        precondition(queue.count == 2)
        let chunk = try JSONSerialization.jsonObject(with: queue[1].payload) as! [String: Any]
        precondition(chunk["uploadedAt"] is [String: Any])
        // Failed/unacknowledged requests remain queued across process restarts.
        db = nil
        db = try Database(storeURL: url)
        try db!.prepareCommutes()
        precondition(try! db!.pendingCount() == 3) // includes interrupted-session final metadata
        let resumed = try db!.pending()
        precondition(resumed[1].path == queue[1].path)
        precondition(resumed[1].payload == queue[1].payload)
        precondition(try! db!.journeys()[0].completed == false)
        precondition(try! db!.journeys()[0].ended != nil)
        try db!.acknowledge(queue[0].id)
        precondition(try! db!.pendingCount() == 2)
        let routeURL = try db!.exportRoute(db!.journeys()[0])
        let csv = try String(contentsOf: routeURL, encoding: .utf8)
        precondition(csv.contains("53.34,-6.25,5.0,"))
        let raw = try db!.export(db!.recordings()[0])
        precondition(try! String(contentsOf: raw, encoding: .utf8).contains("123.0,0.0,0.0,1.0"))
        try db!.bindCloud(uid: "alice", databaseURL: "https://example.firebaseio.com")
        try db!.bindCloud(uid: "alice", databaseURL: "https://example.firebaseio.com")
        do {
            try db!.bindCloud(uid: "bob", databaseURL: "https://example.firebaseio.com")
            fatalError("Cross-account upload binding was accepted")
        } catch { /* expected */ }
        do {
            try db!.bindCloud(uid: "alice", databaseURL: "https://other.firebaseio.com")
            fatalError("Cross-project upload binding was accepted")
        } catch { /* expected */ }
        func journey(_ seconds: Double, route: String = "To college", completed: Bool = true) -> Journey {
            Journey(id: UUID().uuidString, route: route, started: 1000, ended: 1000 + seconds, completed: completed, distance: 500, locationCount: 10)
        }
        precondition(CommuteEstimate.minutes(route: "To college", journeys: [journey(600), journey(900)]) == nil)
        let journeys = [journey(600), journey(1200), journey(900), journey(9000, completed: false), journey(6000, route: "Return home")]
        precondition(CommuteEstimate.minutes(route: "To college", journeys: journeys) == 15)
        try WeatherChecks.run()
        print("PASS: persistent outbox, stable retry path, interrupted recovery, CSV export, account/project isolation, arrival baseline")
    }
}
