import SwiftUI

#if canImport(UIKit)
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

#endif

import Foundation
import Security

struct CloudConfiguration: Codable {
    var databaseURL = "https://urban-computing-a2-default-rtdb.europe-west1.firebasedatabase.app"
    var apiKey = ""
    var enabled = false

    static func load() -> Self {
        guard let data = UserDefaults.standard.data(forKey: "commuteCloud"), let value = try? JSONDecoder().decode(Self.self, from: data) else { return Self() }
        return value
    }
    func save() { UserDefaults.standard.set(try? JSONEncoder().encode(self), forKey: "commuteCloud") }
    func validate() throws {
        guard let url = URL(string: databaseURL), url.scheme == "https", let host = url.host,
              host.hasSuffix(".firebasedatabase.app") || host.hasSuffix(".firebaseio.com"),
              url.path.isEmpty || url.path == "/", url.query == nil, url.user == nil, !apiKey.isEmpty, apiKey.allSatisfy({ $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "-" || $0 == "_") }) else {
            throw CloudFailure.message("Enter the HTTPS Firebase Realtime Database root URL and Web API key.")
        }
    }
}

enum CloudFailure: LocalizedError {
    case message(String)
    var errorDescription: String? { if case .message(let text) = self { return text }; return nil }
}

private struct CloudIdentity: Codable {
    let databaseURL: String
    let uid: String
    let refreshToken: String
}

@MainActor
final class CloudSync {
    private var token: String?
    private var expires = Date.distantPast
    private var authTask: Task<(String, String), Error>?
    private let service = "CommuteWalk.FirebaseIdentity"

    private func identity() throws -> CloudIdentity? {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service, kSecAttrAccount as String: "emailPassword", kSecReturnData as String: true, kSecMatchLimit as String: kSecMatchLimitOne]
        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        if status == errSecItemNotFound { return nil }
        guard status == errSecSuccess, let data = item as? Data else { throw CloudFailure.message("Cannot read cloud identity from Keychain. Unlock the phone and retry.") }
        return try JSONDecoder().decode(CloudIdentity.self, from: data)
    }

    private func saveIdentity(_ value: CloudIdentity) throws {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service, kSecAttrAccount as String: "emailPassword"]
        let attributes: [String: Any] = [kSecValueData as String: try JSONEncoder().encode(value), kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly]
        let status = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        if status == errSecItemNotFound {
            guard SecItemAdd(query.merging(attributes) { _, new in new } as CFDictionary, nil) == errSecSuccess else { throw CloudFailure.message("Cannot persist cloud identity.") }
        } else if status != errSecSuccess { throw CloudFailure.message("Cannot update cloud identity.") }
    }

    private func request(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let response = response as? HTTPURLResponse else { throw CloudFailure.message("No cloud response.") }
        guard (200..<300).contains(response.statusCode) else {
            if response.statusCode == 401 { token = nil; expires = .distantPast }
            // Only translate recognized error codes; never display raw authentication responses.
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let details = json["error"] as? [String: Any], let code = details["message"] as? String {
                switch code {
                case "INVALID_LOGIN_CREDENTIALS", "INVALID_PASSWORD", "EMAIL_NOT_FOUND":
                    throw CloudFailure.message("Email or password not accepted. Use the account created in Firebase Authentication → Users, or reset your password.")
                case "OPERATION_NOT_ALLOWED", "PASSWORD_LOGIN_DISABLED":
                    throw CloudFailure.message("Enable Email/Password in Firebase Authentication → Sign-in method.")
                case "API_KEY_INVALID", "API key not valid. Please pass a valid API key.":
                    throw CloudFailure.message("Firebase API key not accepted. Check the key in your saved project settings.")
                case "USER_DISABLED":
                    throw CloudFailure.message("This Firebase account is disabled. Check Authentication → Users.")
                case "TOO_MANY_ATTEMPTS_TRY_LATER":
                    throw CloudFailure.message("Too many sign-in attempts. Wait before trying again.")
                default: break
                }
            }
            // Never display response bodies, which can contain authentication details.
            throw CloudFailure.message("Firebase HTTP \(response.statusCode). Check Email/Password Authentication, sign-in, database URL, API key and rules; queued data is retained.")
        }
        return data
    }

    private func authenticate(_ config: CloudConfiguration) async throws -> (String, String) {
        if let authTask { return try await authTask.value }
        let task = Task { try await self.authenticateImpl(config) }
        authTask = task
        defer { authTask = nil }
        return try await task.value
    }

    private func authenticateImpl(_ config: CloudConfiguration) async throws -> (String, String) {
        try config.validate()
        let stored = try identity()
        if let stored, stored.databaseURL != config.databaseURL {
            throw CloudFailure.message("Use the original database to preserve ownership of pending journeys.")
        }
        if let stored, let token, expires > Date() { return (stored.uid, token) }
        guard let stored else { throw CloudFailure.message("Sign in with your Firebase email/password account first.") }
        let url = URL(string: "https://securetoken.googleapis.com/v1/token?key=\(config.apiKey)")!
        var encoded = URLComponents()
        encoded.queryItems = [URLQueryItem(name: "grant_type", value: "refresh_token"), URLQueryItem(name: "refresh_token", value: stored.refreshToken)]
        let body = Data((encoded.percentEncodedQuery ?? "").utf8)
        let contentType = "application/x-www-form-urlencoded"
        var req = URLRequest(url: url, timeoutInterval: 20)
        req.httpMethod = "POST"; req.httpBody = body; req.setValue(contentType, forHTTPHeaderField: "Content-Type")
        let responseData = try await request(req)
        let json = try JSONSerialization.jsonObject(with: responseData) as? [String: Any]
        guard let json, let id = (json["localId"] ?? json["user_id"]) as? String,
              let freshToken = (json["idToken"] ?? json["id_token"]) as? String,
              let refresh = (json["refreshToken"] ?? json["refresh_token"]) as? String else {
            throw CloudFailure.message("Firebase returned an invalid authentication response.")
        }
        if stored.uid != id { throw CloudFailure.message("Cloud identity changed unexpectedly.") }
        try saveIdentity(CloudIdentity(databaseURL: config.databaseURL, uid: id, refreshToken: refresh))
        token = freshToken
        expires = Date().addingTimeInterval(3300)
        return (id, freshToken)
    }

    func storedUID(config: CloudConfiguration) throws -> String? {
        guard let stored = try identity() else { return nil }
        guard stored.databaseURL == config.databaseURL else { throw CloudFailure.message("Use the Firebase database linked to your saved account.") }
        return stored.uid
    }

    func signIn(email: String, password: String, config: CloudConfiguration) async throws -> String {
        try config.validate()
        guard !email.isEmpty, !password.isEmpty else { throw CloudFailure.message("Enter your email and password.") }
        var req = URLRequest(url: URL(string: "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=\(config.apiKey)")!, timeoutInterval: 20)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: ["email": email, "password": password, "returnSecureToken": true])
        let data = try await request(req)
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let uid = json["localId"] as? String, let token = json["idToken"] as? String,
              let refresh = json["refreshToken"] as? String else { throw CloudFailure.message("Invalid sign-in response.") }
        try saveIdentity(CloudIdentity(databaseURL: config.databaseURL, uid: uid, refreshToken: refresh))
        self.token = token; expires = Date().addingTimeInterval(3300)
        return uid
    }

    func signOut() throws {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service, kSecAttrAccount as String: "emailPassword"]
        let result = SecItemDelete(query as CFDictionary)
        guard result == errSecSuccess || result == errSecItemNotFound else { throw CloudFailure.message("Could not clear sign-in from Keychain.") }
        token = nil; expires = .distantPast
    }

    func resetPassword(email: String, config: CloudConfiguration) async throws {
        try config.validate()
        guard !email.isEmpty else { throw CloudFailure.message("Enter your account email first.") }
        var req = URLRequest(url: URL(string: "https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key=\(config.apiKey)")!, timeoutInterval: 20)
        req.httpMethod = "POST"; req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: ["requestType": "PASSWORD_RESET", "email": email])
        _ = try await request(req)
    }

    func upload(_ pending: PendingUpload, config: CloudConfiguration, expectedUID: String) async throws -> String {
        let (uid, token) = try await authenticate(config)
        guard uid == expectedUID else { throw CloudFailure.message("Sign into the account that owns this phone’s local journeys.") }
        let root = config.databaseURL.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        var components = URLComponents(string: "\(root)/users/\(uid)/\(pending.path).json")!
        components.queryItems = [URLQueryItem(name: "auth", value: token)]
        var req = URLRequest(url: components.url!, timeoutInterval: 20)
        // Deterministic paths make retries safe if the server accepted a request before disconnection.
        req.httpMethod = "PUT"; req.httpBody = pending.payload
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        _ = try await request(req)
        return uid
    }


}

struct WeatherSnapshot: Decodable {
    let observedAt: Double
    let fetchedAt: Double
    let temperatureC: Double?
    let rainfallMM: Double?
    let windSpeedKnots: Double?
    let description: String
    var stale: Bool { Date().timeIntervalSince1970 - observedAt / 1000 > 7200 }
}

struct OpenWeatherObservation {
    let id: String
    let payload: Data
    let snapshot: WeatherSnapshot
}

enum OpenWeather {
    static let sourceURL = URL(string: "https://prodapi.met.ie/observations/dublin/today")!

    static func collect() async throws -> [OpenWeatherObservation] {
        var request = URLRequest(url: sourceURL, timeoutInterval: 20)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let response = response as? HTTPURLResponse, (200..<300).contains(response.statusCode) else {
            throw CloudFailure.message("Weather provider did not return a successful response.")
        }
        return try normalize(data: data, fetchedAt: Date())
    }

    static func normalize(data: Data, fetchedAt: Date) throws -> [OpenWeatherObservation] {
        guard let rows = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] else {
            throw CloudFailure.message("Unexpected weather response format.")
        }
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "Europe/Dublin")
        formatter.dateFormat = "dd-MM-yyyy HH:mm"
        formatter.isLenient = false
        func number(_ value: Any?, min: Double, max: Double) -> Any {
            guard let value, !(value is NSNull), let result = Double(String(describing: value).trimmingCharacters(in: .whitespacesAndNewlines)), result.isFinite, result >= min, result <= max else { return NSNull() }
            return result
        }
        var observations: [OpenWeatherObservation] = []
        for raw in rows {
            guard raw["name"] as? String == "Dublin Airport", let date = raw["date"] as? String, let time = raw["reportTime"] as? String else { continue }
            let local = "\(date) \(time)"
            guard let observed = formatter.date(from: local), formatter.string(from: observed) == local,
                  observed.timeIntervalSince(fetchedAt) <= 300,
                  formatter.string(from: observed.addingTimeInterval(3600)) != local,
                  formatter.string(from: observed.addingTimeInterval(-3600)) != local else { continue }
            let milliseconds = observed.timeIntervalSince1970 * 1000
            let id = String(Int64(milliseconds))
            let payload: [String: Any] = [
                "id": id, "station": "dublin-airport", "stationLatitude": 53.428, "stationLongitude": -6.241,
                "observedAt": milliseconds, "fetchedAt": fetchedAt.timeIntervalSince1970 * 1000,
                "temperatureC": number(raw["temperature"], min: -50, max: 60),
                "rainfallMM": number(raw["rainfall"], min: 0, max: 500),
                "windSpeedKnots": number(raw["windSpeed"], min: 0, max: 200),
                "description": (raw["weatherDescription"] as? String ?? "Unavailable").trimmingCharacters(in: .whitespacesAndNewlines),
                "sourceURL": sourceURL.absoluteString, "source": "Met Éireann", "licence": "CC BY 4.0",
                "modified": "Numeric fields parsed and unambiguous Europe/Dublin local times converted to UTC milliseconds. Raw fields retained.",
                "raw": raw, "uploadedAt": [".sv": "timestamp"]
            ]
            let encoded = try JSONSerialization.data(withJSONObject: payload)
            observations.append(OpenWeatherObservation(id: id, payload: encoded, snapshot: try JSONDecoder().decode(WeatherSnapshot.self, from: encoded)))
        }
        guard !observations.isEmpty else { throw CloudFailure.message("No valid Dublin Airport observations; existing data retained.") }
        return observations.sorted { $0.snapshot.observedAt < $1.snapshot.observedAt }
    }
}
