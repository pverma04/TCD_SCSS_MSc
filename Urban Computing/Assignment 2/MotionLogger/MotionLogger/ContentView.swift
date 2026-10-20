import SwiftUI

struct ContentView: View {
    @ObservedObject var recorder: Recorder

    var body: some View {
        NavigationStack {
            List {
                Section("Capture") {
                    Label(recorder.isRecording ? "Recording • \(recorder.count) samples saved" : "Ready to record", systemImage: recorder.isRecording ? "record.circle.fill" : "waveform.path")
                        .foregroundStyle(recorder.isRecording ? .red : .primary)
                    HStack {
                        axis("X", recorder.x)
                        axis("Y", recorder.y)
                        axis("Z", recorder.z)
                    }
                    HStack {
                        Button("Start", systemImage: "record.circle", action: recorder.start)
                            .tint(.green)
                            .disabled(recorder.isRecording)
                        Spacer()
                        Button("End", systemImage: "stop.circle", action: recorder.end)
                            .tint(.red)
                            .disabled(!recorder.isRecording)
                    }
                    .buttonStyle(.borderedProminent)
                    Text("50 Hz requested · acceleration in g, including gravity. Keep the app open; capture ends in the background.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Section("Saved recordings") {
                    if recorder.recordings.isEmpty {
                        Text("Tap Start to create your first recording.").foregroundStyle(.secondary)
                    }
                    ForEach(recorder.recordings) { recording in
                        VStack(alignment: .leading, spacing: 8) {
                            Text(recording.started.formatted(date: .abbreviated, time: .standard)).font(.headline)
                            if let ended = recording.ended {
                                Text("\(recording.count) samples · \(Int(max(0, ended.timeIntervalSince(recording.started)))) seconds")
                                    .font(.subheadline).foregroundStyle(.secondary)
                                Button("Prepare CSV", systemImage: "square.and.arrow.up") { recorder.export(recording) }
                                    .disabled(recorder.isRecording)
                            } else {
                                Text("Recording in progress…").foregroundStyle(.secondary)
                            }
                        }.padding(.vertical, 4)
                    }
                }
                if let url = recorder.exportURL {
                    Section("Export ready") {
                        ShareLink("Share CSV", item: url)
                        Text("Save to Files, AirDrop, or choose another destination.").font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("Motion Logger")
            .alert("Motion Logger", isPresented: Binding(get: { recorder.errorMessage != nil }, set: { if !$0 { recorder.errorMessage = nil } })) {
                Button("OK") { recorder.errorMessage = nil }
            } message: { Text(recorder.errorMessage ?? "") }
        }
    }

    private func axis(_ name: String, _ value: Double) -> some View {
        VStack {
            Text(name).foregroundStyle(.secondary)
            Text(value, format: .number.precision(.fractionLength(3))).monospacedDigit()
        }.frame(maxWidth: .infinity)
    }
}
