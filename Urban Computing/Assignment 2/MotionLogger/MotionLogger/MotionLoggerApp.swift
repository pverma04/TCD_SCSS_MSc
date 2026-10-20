import SwiftUI

@main
struct MotionLoggerApp: App {
    @StateObject private var recorder = Recorder()
    @Environment(\.scenePhase) private var phase

    var body: some Scene {
        WindowGroup {
            ContentView(recorder: recorder)
                .onChange(of: phase) { _, phase in
                    if phase == .background { recorder.end() }
                }
        }
    }
}
