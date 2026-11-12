# CommuteWalk - Urban Computing Assignment 2

SwiftUI iPhone application extending the original MotionLogger. It records your own walking journeys, streams accelerometer/GPS data to Firebase Realtime Database, and collects Met Éireann's live hourly Dublin Airport observations into the same private Firebase account. The app checks the weather source every minute while it is open.

**Current status (6 November 2026):** the app builds and is installed on the user's iPhone; local storage/parser checks pass. The user confirmed successful authenticated uploads, zero queued records, and both journeys/weather branches present in Firebase after publishing the supplied rules. The user also confirmed sample-containing chunks arrive while recording, demonstrating live own-data upload. Full walking-route validation, measured latency, automatic ingestion across a new weather update and adversarial rule checks remain pending. The report draft states these limits explicitly.

## Smallest complete setup

No Firebase SDK, npm packages, paid scheduler, backend server or service-account key is needed. The app uses HTTPS REST endpoints, Firebase Email/Password Authentication, and the supplied database rules.

1. Firebase project: `urban-computing-a2`.
2. Database region: Belgium (`europe-west1`). URL: `https://urban-computing-a2-default-rtdb.europe-west1.firebasedatabase.app`.
3. In Firebase Console, enable **Authentication > Sign-in method > Email/Password**. Anonymous Authentication may remain disabled.
4. Under **Authentication > Users > Add user**, create your own email/password user. Keep the password private.
5. Under **Realtime Database > Rules**, replace the rules with the complete contents of `cloud/database.rules.json`, then **Publish**. These rules grant each authenticated user access only to their own `users/<uid>` branch. Do not enable public test-mode rules.
6. Obtain the app API key: Project settings > General > Your apps. If needed, register an Apple app with bundle ID `com.example.MotionLogger`; download `GoogleService-Info.plist` and read its `API_KEY`. This app does not require adding that file to Xcode or installing Firebase SDKs. If you changed the bundle ID in Xcode, register the actual ID instead.
7. Open `MotionLogger.xcodeproj` in Xcode 15 or newer. Select the MotionLogger target, choose your signing team, and select your **physical iPhone**, not a simulator. Requires iOS 17 or newer. Enable Developer Mode and trust the developer profile if prompted. Build and run.
8. In the app, choose **Configure Firebase**, paste your database URL/API key, enable **Upload my recorded journeys**, and choose **Save project settings**. Sign in with the account from step 4. Passwords are not stored; a refresh token is stored in iOS Keychain.
9. Allow location access. Tap **Start**, walk with the app open, then choose **Arrived**. Choose **End early** for incomplete walks. Going into the background ends capture as incomplete.
10. Watch the Firebase Data tab at `users/<uid>/journeys` and `users/<uid>/weather/dublin-airport/observations`. The app displays its UID and server-acknowledged upload time. Follow `docs/DEMONSTRATION.md` before reporting success.

The API key is Firebase app configuration, not an administrator credential. Access protection comes from authentication and rules. Do not put passwords, refresh tokens, service-account private keys or other administrator credentials in source code or your submission.

## What runs where

- **iPhone:** Core Motion (one sample every 5 s), GPS callbacks, Start/Arrived/End early controls, SQLite storage, durable upload queue, email/password sign-in, HTTPS uploads and weather collection every 60 seconds while open.
- **Firebase Authentication:** validates the user's email/password and issues/refreshes identity tokens.
- **Firebase Realtime Database, Belgium:** JSON journey metadata, motion/GPS chunks and open weather observations. Rules isolate each UID. Server timestamps record receipt time.
- **Met Éireann:** publishes the Dublin Airport observation endpoint, nominally hourly. The phone reads JSON via HTTPS. No component runs periodically when the app is closed.

Editable diagrams and report material: `docs/architecture.mmd`, `docs/report-draft.md`. PDF report draft and ZIP are in the workspace's `submission/` directory after running the packaging tool.

The current build requests one accelerometer sample every 5 seconds (0.2 Hz). A sensor-timestamp guard also rejects callbacks arriving less than 5 seconds after the last saved motion sample. This applies to new recordings; earlier data retains its original timestamps. One-second upload batching is unchanged. Use sensor timestamps to measure the actual delivered rate.

## Data format and joining the sources

```
users/<firebase-uid>/
  journeys/<session-uuid>/
    metadata: route, startedAt, endedAt, completed, distanceMeters,
              locationCount, station, schemaVersion, uploadedAt
    chunks/<chunk-uuid>: capturedAt, motion[], locations[], uploadedAt
  weather/dublin-airport/observations/<observation-unix-ms>:
    station, observedAt, fetchedAt, uploadedAt, temperatureC,
    rainfallMM, windSpeedKnots, description, sourceURL, licence, raw
```

Journey metadata and weather times are UTC Unix **milliseconds**. Within sample arrays, sensor/GPS `timestamp`, sensor `uptime`, and chunk `capturedAt` are **seconds**. Motion X/Y/Z units are **g**, including gravity. GPS is WGS84 latitude/longitude in degrees, accuracy in meters, speed in meters/second when valid. `uploadedAt` is a Firebase server timestamp in milliseconds. Weather wind remains in **knots**; rainfall is the provider's hourly reading in **mm**.

The shared `station = dublin-airport` and timestamps enable a temporal join. For a journey, select the latest station observation at or before `metadata.startedAt`, then check its age. Observations older than two hours must be labelled stale; they must not be silently used as current conditions. The app displays latest available weather and its age, but does not yet predict weather-dependent walking times. The station is a fixed Dublin context, not an automatically chosen nearest station or a street-level measurement.

The optional arrival baseline uses the median duration of at least three explicitly completed, GPS-bearing walks with the same direction label. Use each label consistently for the same route/endpoints. This is a personal baseline, not a forecast or a guarantee. Weather-based prediction is deferred to Assignment 3.

## Reliability and privacy

- Motion samples are saved individually in the existing `motion.sqlite` database. GPS/motion chunks enter a persistent SQLite outbox approximately every second. Existing original accelerometer sessions are retained.
- Outbox entries are removed only after Firebase returns a successful HTTP response. Retries reuse the same UUID-based path, preventing duplicate chunks. Backoff increases to at most 60 seconds after failures; **Retry sync** resets it.
- On relaunch, unfinished journeys are marked incomplete. An abrupt termination may leave up to approximately one second of not-yet-chunked GPS/cloud data unavailable; individually saved raw motion remains local. This is not background capture. Recovery end time is the relaunch time for the new journey metadata, and interrupted journeys are excluded from the baseline.
- The local database is bound to the first successfully signed-in UID and database URL. Reauthentication with that account works; uploading this database to another account/project is blocked. This small assignment app does not merge local journey histories across devices or offer multi-user local profiles.
- GPS rejects poor fixes (>50 m stated accuracy), old/out-of-order points and jumps above 5 m/s. Distance remains approximate.
- Weather observations use deterministic time IDs and persistent local deduplication. Missing/invalid readings remain null. The provider reports local Irish time; the parser converts unambiguous timestamps to UTC and skips ambiguous/nonexistent DST hours.
- Precise GPS/motion are private within your Firebase account. Exported CSVs contain location/movement data. Do not upload personal journey exports to the source ZIP or publish the database publicly.
- Weather observations can be stale or unavailable. The app reports source failures and observation age instead of synthesizing readings. User-owned weather copies are authenticated client uploads, not server-attested measurements.

## Run the local checks

From this directory, on a Mac with Xcode command-line tools installed:

```sh
sh tests/run_checks.sh
```

This compiles and runs the real SQLite storage, weather parser and baseline logic against isolated temporary databases. It tests offline persistence, stable retry paths, recovery, CSV exports, account/project binding, missing weather readings, timezone/DST handling, sorting, and weather deduplication. It does not use your Firebase credentials or upload data. iOS build validation is performed through Xcode. Firebase rules/auth/network and physical sensor behavior require the separate live checks.

## Open-data attribution

Copyright Met Éireann. Source: https://www.met.ie/ . Data is published under CC BY 4.0: https://creativecommons.org/licenses/by/4.0/ . Met Éireann does not accept liability for errors, omissions, availability or losses arising from use. This application modifies the source by parsing numeric values and converting unambiguous local timestamps to UTC; raw fields are retained. Dataset and field definitions: https://data.gov.ie/dataset/todays-weather-dublin-airport . Feed: https://prodapi.met.ie/observations/dublin/today . The dataset is not quality controlled.

## Blackboard submission

Submit separately and in this order: (1) short report PDF or Word, (2) source ZIP including these instructions. Complete the live evidence checklist and replace pending statements with measured outcomes before producing a final report. No live success is claimed by the supplied draft.
