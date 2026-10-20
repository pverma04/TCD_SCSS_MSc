# Motion Logger

A SwiftUI iPhone/iPad app for collecting raw accelerometer data in a local SQLite database and exporting individual recording sessions as CSV. Requires iOS 17 or later and Xcode 15 or later. No external packages or server are required.

## Run after Xcode finishes installing

1. Open Xcode once, accept its license and install the iOS platform components it requests.
2. Open `MotionLogger.xcodeproj`.
3. Select the **MotionLogger** target, open **Signing & Capabilities**, and choose your Apple development team. Change `com.example.MotionLogger` to your own unique bundle identifier if needed.
4. Connect and trust your iPhone, enable Developer Mode if requested, select it as the run destination, and press Run.
5. Tap **Start**, move the phone, then tap **End**. Choose **Prepare CSV** for a saved recording, then **Share CSV** → Save to Files or AirDrop.

The simulator can display the interface but has no physical accelerometer. Use an actual device to record.

## Data and behavior

- Requests 50 samples/second through Core Motion. Actual timing depends on the device; use the sensor timestamps to calculate the delivered rate.
- X/Y/Z are raw device-coordinate acceleration in **g**, including gravity. These are not gravity-removed measurements.
- CSV columns: `session_id,timestamp_utc,unix_seconds,sensor_uptime_seconds,x_g,y_g,z_g`.
- Wall-clock sample timestamps are estimated from a wall-clock/uptime anchor captured at session start. Sensor uptime preserves monotonic timing independently of clock changes.
- Every delivered sample is committed to SQLite before the saved-sample counter advances. Database errors stop capture and display an alert.
- Database: `Library/Application Support/motion.sqlite` inside the app sandbox, using SQLite WAL journaling. It persists between app launches. Uninstalling the app removes its local data.
- Capture ends when the app enters the background. The screen stays awake during capture. It does not implement background or locked-screen collection.
- If the app is terminated unexpectedly, the next launch closes an unfinished session using its last saved sample time. An empty interrupted session uses its start time.
- CSV exports are generated in the app's temporary Exports folder. Share or save them elsewhere for durable access. Export is disabled while recording.

## Implementation and validation

`Recorder.swift` manages Core Motion and recording state; `Database.swift` handles SQLite and streaming CSV output; `ContentView.swift` provides capture controls and history.

This scaffold uses main-queue capture and synchronous per-sample database writes for simplicity and immediate persistence. For high sampling rates or extended collection, move persistence onto a dedicated serial queue and measure dropped samples and UI responsiveness on the target device.

Project property-list validation and Swift syntax parsing were performed. A full iOS build and hardware verification require the completed Xcode installation. Before collecting important data, record a short session, relaunch the app, export it, and check timestamps, sample count, and stationary gravity readings (vector magnitude around 1 g). Also check background stopping and restart behavior.
