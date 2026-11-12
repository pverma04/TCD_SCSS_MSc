import SwiftUI
import MapKit

struct ContentView: View {
    @ObservedObject var recorder: Recorder
    @State private var showSettings = false
    @State private var arrival = Date()

    var body: some View {
        NavigationStack {
            List {
                Section("Your walking commute") {
                    Picker("Direction", selection: $recorder.route) {
                        Text("To college").tag("To college")
                        Text("Return home").tag("Return home")
                    }.disabled(recorder.isRecording)
                    if let minutes = recorder.estimatedMinutes {
                        Label("Typical walk: \(minutes) min", systemImage: "figure.walk")
                        DatePicker("Arrive by", selection: $arrival, displayedComponents: .hourAndMinute)
                        Text("Leave around \(arrival.addingTimeInterval(-Double(minutes * 60)).formatted(date: .omitted, time: .shortened))")
                            .font(.headline)
                        Text("Median of your completed walks in this direction. No weather adjustment yet; choose your own extra buffer.")
                            .font(.caption).foregroundStyle(.secondary)
                    } else {
                        Text("Record 3 completed walks in this direction to get a typical journey time.")
                            .foregroundStyle(.secondary)
                    }
                    Text("Use each direction label for the same route and endpoints. Keep the app open and phone placement consistent.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Section("Record a journey") {
                    Label(recorder.isRecording ? "Recording · \(recorder.count) motion samples" : "Ready to walk", systemImage: "figure.walk")
                    Text("\(Int(recorder.distance)) m · \(recorder.locationCount) GPS points")
                        .monospacedDigit()
                    LocationStatus(location: recorder.location)
                    HStack {
                        Button("Start", systemImage: "record.circle", action: recorder.start)
                            .disabled(recorder.isRecording)
                        Spacer()
                        Button("Arrived", systemImage: "flag.checkered", action: recorder.arrive)
                            .disabled(!recorder.isRecording)
                    }.buttonStyle(.borderedProminent)
                    if recorder.isRecording {
                        Button("End early", role: .destructive, action: recorder.end)
                    }
                    Text("One motion sample every 5 seconds · foreground only. Locking or leaving the app can interrupt capture; interrupted walks are excluded from estimates.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Section("Cloud sync") {
                    Label(recorder.cloudStatus, systemImage: "icloud")
                        .font(.subheadline)
                    Text("\(recorder.pendingCount) queued records")
                    if let uploaded = recorder.lastUploaded {
                        Text("Last confirmed: \(uploaded.formatted(date: .omitted, time: .standard))").font(.caption)
                    }
                    if !recorder.cloudUID.isEmpty {
                        Text("User: \(recorder.cloudUID)").font(.caption).textSelection(.enabled)
                    }
                    Button("Retry sync") { recorder.sync(force: true); recorder.refreshWeather() }
                        .disabled(!recorder.configuration.enabled)
                    Button("Configure Firebase") { showSettings = true }.disabled(recorder.isRecording)
                }
                Section("Dublin Airport weather") {
                    Text(recorder.weatherStatus).font(.caption)
                    if let weather = recorder.weather {
                        Text(weather.description)
                        HStack {
                            if let temp = weather.temperatureC { Text("\(temp, specifier: "%.0f") °C") }
                            if let rain = weather.rainfallMM { Text("Rain \(rain, specifier: "%.2f") mm") }
                            if let wind = weather.windSpeedKnots { Text("Wind \(wind, specifier: "%.0f") kt") }
                        }.font(.subheadline)
                        Text("Observed \(Date(timeIntervalSince1970: weather.observedAt / 1000).formatted())")
                            .font(.caption)
                        if weather.stale { Label("Stale observation · over 2 hours old", systemImage: "exclamationmark.triangle").foregroundStyle(.orange) }
                    }
                    Text("Checked every minute while this app is open; source measurements update hourly. Not a forecast or street-level measurement. Source: Met Éireann · CC BY 4.0.")
                        .font(.caption).foregroundStyle(.secondary)
                    Link("Weather source and licence", destination: URL(string: "https://data.gov.ie/dataset/todays-weather-dublin-airport")!)
                }
                Section("Journey history") {
                    if recorder.journeys.isEmpty { Text("Your completed and interrupted walks will appear here.").foregroundStyle(.secondary) }
                    ForEach(recorder.journeys) { journey in
                        VStack(alignment: .leading, spacing: 6) {
                            Text(journey.route).font(.headline)
                            Text(Date(timeIntervalSince1970: journey.started).formatted()).font(.caption)
                            Text(journey.ended == nil ? "Recording" : (journey.completed ? "Completed" : "Interrupted / ended early"))
                                .foregroundStyle(.secondary)
                            Text("\(Int(journey.distance)) m · \(journey.locationCount) GPS points")
                            if let ended = journey.ended {
                                Text("\(Int(max(0, ended - journey.started) / 60)) min")
                                Button("Export GPS CSV") { recorder.exportRoute(journey) }.disabled(recorder.isRecording)
                            }
                        }.padding(.vertical, 4)
                    }
                }
                Section("Motion recordings (including earlier sessions)") {
                    ForEach(recorder.recordings) { recording in
                        if recording.ended != nil {
                            Button("\(recording.started.formatted()) · \(recording.count) samples") { recorder.export(recording) }
                                .disabled(recorder.isRecording)
                        }
                    }
                }
                if let url = recorder.exportURL {
                    Section("Export ready") { ShareLink("Share CSV", item: url) }
                }
            }
            .navigationTitle("CommuteWalk")
            .sheet(isPresented: $showSettings) { CloudSettings(recorder: recorder) }
            .alert("CommuteWalk", isPresented: Binding(get: { recorder.errorMessage != nil }, set: { if !$0 { recorder.errorMessage = nil } })) {
                Button("OK") { recorder.errorMessage = nil }
            } message: { Text(recorder.errorMessage ?? "") }
        }
    }

}

private struct LocationStatus: View {
    @ObservedObject var location: WalkLocation
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(location.status).font(.caption).foregroundStyle(.secondary)
            if !location.points.isEmpty {
                Map {
                    MapPolyline(coordinates: location.points).stroke(.blue, lineWidth: 4)
                }.frame(height: 180).clipShape(RoundedRectangle(cornerRadius: 12))
            }
        }
    }
}


private struct CloudSettings: View {
    @ObservedObject var recorder: Recorder
    @Environment(\.dismiss) private var dismiss
    @State private var draft: CloudConfiguration
    @State private var email = ""
    @State private var password = ""

    init(recorder: Recorder) {
        self.recorder = recorder
        _draft = State(initialValue: recorder.configuration)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("1. Project settings") {
                    TextField("Realtime Database HTTPS URL", text: $draft.databaseURL)
                        .textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL)
                    TextField("Firebase Web API key", text: $draft.apiKey)
                        .textInputAutocapitalization(.never).autocorrectionDisabled()
                    Toggle("Upload my recorded journeys", isOn: $draft.enabled)
                    Text("Uploads send precise GPS routes and movement samples, including queued journeys, to your Firebase project. Save settings before signing in. Passwords are not stored; the session refresh token is stored in iOS Keychain.")
                        .font(.caption)
                    Button("Save project settings") { recorder.saveConfiguration(draft) }
                        .disabled(recorder.syncing || recorder.accountBusy)
                }
                Section("2. Your Firebase account") {
                    if recorder.cloudUID.isEmpty {
                        TextField("Email", text: $email).keyboardType(.emailAddress)
                            .textInputAutocapitalization(.never).autocorrectionDisabled().textContentType(.username)
                        SecureField("Password", text: $password).textContentType(.password)
                        Button(recorder.accountBusy ? "Connecting…" : "Sign in") {
                            let enteredPassword = password
                            password = ""
                            Task { await recorder.signIn(email: email, password: enteredPassword) }
                        }.disabled(recorder.accountBusy || recorder.syncing)
                        Button("Reset password") { Task { await recorder.resetPassword(email: email) } }
                            .disabled(recorder.accountBusy)
                        Text("Create your account in Firebase Console → Authentication → Users → Add user. Enable Email/Password as the provider. Anonymous sign-in is not used.")
                            .font(.caption)
                    } else {
                        Text("Signed in: \(recorder.cloudUID)").font(.caption).textSelection(.enabled)
                        Button("Sign out", role: .destructive, action: recorder.signOut)
                            .disabled(recorder.syncing || recorder.accountBusy)
                        Text("The local database remains linked to this account to prevent uploading private journeys to another account.")
                            .font(.caption)
                    }
                }
                Text(recorder.cloudStatus).font(.caption)
            }
            .navigationTitle("Firebase connection")
            .toolbar { Button("Done") { dismiss() } }
            .alert("CommuteWalk", isPresented: Binding(get: { recorder.errorMessage != nil }, set: { if !$0 { recorder.errorMessage = nil } })) {
                Button("OK") { recorder.errorMessage = nil }
            } message: { Text(recorder.errorMessage ?? "") }
        }
    }
}
