# CommuteWalk: own walking data and open weather data in Firebase

Urban Computing - Assignment 2. Draft updated 6 November 2026.

## Verification statement

The source builds successfully in Xcode, and isolated storage/parser tests pass. The updated app was installed on the user's physical iPhone. On 6 November 2026, the user confirmed that, after publishing the database rules and signing in, the app displayed “All queued data uploaded” with zero queued records, and both the journeys and weather branches were present under their Firebase user. This is user-confirmed evidence of successful cloud storage, not independent inspection of the remote dataset. The user subsequently confirmed that new journeys and sample-containing chunks appeared in Firebase while recording, before tapping Arrived. This demonstrates live upload of the own-data stream. Measured upload latency, a full walking-route trial and automatic collection across a new weather observation remain pending. No numerical latency or predictive-accuracy results are claimed.

## Purpose and platform

CommuteWalk extends the original SwiftUI accelerometer logger into a walking commute collector. It retains local SQLite recording and CSV export, adds foreground GPS, and sends data to Firebase Realtime Database as JSON. Firebase is explicitly permitted by the assignment. The project is urban-computing-a2, database region europe-west1 (Belgium). Email/password Firebase Authentication and per-UID rules protect precise routes. The key is entered on the phone, not embedded in source; the password is not stored and the refresh token is stored in Keychain.

## Task 1: gathering my data

A physical iPhone captures raw accelerometer data at a requested interval of 5 seconds (0.2 Hz) and GPS updates while a journey is active. The user selects a direction, taps Start, and ends with Arrived or End early. Sensor timestamps are retained; approximate wall-clock motion times derive from an uptime/wall-clock anchor. Motion X/Y/Z are in g including gravity. GPS latitude/longitude use WGS84, stated accuracy is meters and valid speed is meters/second.

The app saves raw motion locally and approximately every second commits motion/GPS chunks to a durable SQLite outbox. Authenticated HTTPS PUT requests write to users/<uid>/journeys/<session>/metadata and chunks/<chunk>. Firebase server uploadedAt timestamps record receipt. Successful responses acknowledge and remove outbox entries; failed requests retain them with increasing retry delay up to 60 seconds. Stable UUID paths avoid duplicate chunks after retries.

Journey metadata times use Unix milliseconds, while sample timestamps and chunk capturedAt use seconds. The diagrams must clearly identify iPhone acquisition/SQLite/uploader, Firebase Auth/rules, and cloud JSON storage. Current own-cloud-data status: confirmed by the user on 6 November 2026. Current real-time-upload status: demonstrated by user observation of sample-containing chunks appearing during recording on 6 November 2026. The user observed chunk creation before ending the recording. Measuring capture/receipt latency and testing recovery after disconnection remain supplementary checks.

## Task 2: gathering open data

The source is Met Eireann's Dublin Airport hourly observations: https://prodapi.met.ie/observations/dublin/today . Its catalogue states hourly updates, local Irish observation times, and that the data is not quality controlled. The same foreground iPhone checks the API every 60 seconds, normalizes numeric values and unambiguous Europe/Dublin times, retains raw fields, and queues new observations for Firebase upload.

Cloud destination: users/<uid>/weather/dublin-airport/observations/<observation-unix-ms>. Records contain temperatureC, rainfallMM, windSpeedKnots, description, sourceURL, licence, observedAt (source measurement), fetchedAt (phone collection), and uploadedAt (server receipt). Observation-time IDs and persistent deduplication avoid storing unchanged hourly readings repeatedly. Missing values remain null. Ambiguous/nonexistent daylight-saving hours are skipped rather than assigned an invented UTC instant.

The ingestion is designed as near-real-time collection of the latest available hourly observations, not second-by-second meteorological measurements. It only runs while the app is open. Live availability, actual observation cadence and upload latency still need demonstration. Current open-cloud-data status: confirmed by the user on 6 November 2026. Current automatic/live-ingestion status: pending observation of a new provider update. Leave the app open across a genuine source update and show a new observation ID appearing automatically; re-fetching an unchanged snapshot is insufficient evidence.

## Combining sources and continuation

Journey metadata includes station=dublin-airport. Station ID and UTC time enable a join to the latest observation at or before journey start, with an explicit freshness check. Observations more than two hours old are marked stale in the interface. Airport weather is contextual, not a street-level or nearest-station measurement. Weather-dependent arrival prediction is deferred to Assignment 3. A small existing baseline uses the median of at least three explicitly completed, GPS-bearing walks in the same direction; interrupted walks are excluded.

## Validation and limitations

Confirmed locally: Xcode build; persistent upload queue across relaunch; stable retry paths; interrupted-session recovery; CSV export; account/project binding; weather schema, numeric/missing readings, Irish timezone and daylight-saving handling; observation sorting and deduplication. The user published the supplied rules and confirmed successful authenticated uploads. Cross-user access isolation, malformed-data rejection, password recovery and offline replay on the physical phone have not yet been demonstrated. No synthetic fixture is reported as the student's own cloud data.

Keep the app foreground and the phone unlocked. Backgrounding ends the journey as incomplete. Abrupt termination may lose approximately the last second of not-yet-chunked GPS/cloud data; individually saved raw motion remains local. The new journey recovery end time is relaunch time, and that interrupted trip is excluded from estimates. Actual sample rate and GPS accuracy vary. Local account binding prevents queued journeys being uploaded to a different user/project; this is a single-account local database and does not merge histories from multiple phones.

## Submission and reproducibility

README.md includes Firebase console setup, the exact bundle ID, rules publication, physical-iPhone run instructions, key entry and local test commands. DEMONSTRATION.md maps all 10 marks to evidence. Submit separately on Blackboard: (1) the short finalized report PDF/Word; (2) the source ZIP with instructions. Keep real demonstrable cloud data available for assessment. This draft must be updated after the walking and live-ingestion tests; it should not be submitted as evidence those pending tests have succeeded.

## References and attribution

1. Met Eireann, Today's weather Dublin Airport: https://data.gov.ie/dataset/todays-weather-dublin-airport
2. Firebase, REST save data: https://firebase.google.com/docs/database/rest/save-data
3. Firebase, Auth REST API: https://firebase.google.com/docs/reference/rest/auth
4. Firebase, API keys: https://firebase.google.com/docs/projects/api-keys

Copyright Met Eireann. Source www.met.ie. CC BY 4.0: https://creativecommons.org/licenses/by/4.0/ . Met Eireann does not accept liability for errors, omissions, availability or loss arising from use. This application modifies the data by parsing numeric fields and converting unambiguous local timestamps to UTC; raw fields are retained.
