# Live verification and evidence checklist

Do these checks using real walking data. Record actual timestamps and results; do not infer cloud success from a successful build or a local CSV.

## Confirmed on 6 November 2026

The user reported “All queued data uploaded”, 0 queued records, and both journeys and weather present under their Firebase UID after publishing the rules. Installation on the physical iPhone is confirmed. The user also confirmed that journeys and sample-containing chunks arrive live during recording, before Arrived. A full walking-route trial, quantitative sample-count/latency review, a new weather-update observation and cross-user rule tests remain unreported.

## Task 1: own source (5 marks)

- [x] Technical architecture: own source diagram identifies iPhone acquisition, SQLite, HTTPS uploader, Firebase Auth/rules and Belgium cloud storage. See PDF draft and architecture.mmd.
- [x] Journey branch in cloud: user confirmed it exists and the upload queue drained on 6 November 2026.
- [ ] Walking-data evidence: record a real short walk and verify nonempty GPS/motion chunks and completed metadata. Save a screenshot with private details cropped.
- [x] Real-time own-data upload: user confirmed sample-containing chunks appear while recording, before Arrived, on 6 November 2026.
- [ ] Quantitative timing evidence: record source/capture times and server `uploadedAt` for several chunks. Report measured latency, not an assumed one-second guarantee.
- [ ] Disconnect internet for 20 seconds while recording. Confirm queued count grows; reconnect and confirm queue drains. Relaunch offline once to confirm queued records persist. There should be one path per original chunk, including after retry.
- [ ] Restart after normal ending: history remains. End early/background a test walk and confirm it is excluded from the arrival estimate.

## Task 2: open source (5 marks)

- [x] Architecture: open source diagram identifies Met Eireann provider, phone's 60-second collector, parsing, SQLite outbox and cloud JSON destination.
- [x] Weather branch in cloud: user confirmed it exists on 6 November 2026.
- [ ] Review stored weather fields: check `sourceURL`, raw fields, `observedAt`, `fetchedAt`, server `uploadedAt` and units. Save a screenshot.
- [ ] Leave the app open across a provider observation update, and verify a new observation ID appears automatically. Polling unchanged data is not evidence of new real-time measurements. Confirm at least two source observation times without manual imports.
- [ ] Record actual source cadence/freshness. The chosen source publishes hourly, and checks run every minute only while the app is open. Call it near-real-time ingestion of hourly observations, not a second-by-second weather sensor.
- [ ] If the provider is stale, report that honestly. Do not replace its timestamp with collection time or claim a stale snapshot is current.

## Access control and final handover

- [x] Supplied rules published; authenticated upload succeeds (user-confirmed).
- [ ] Access-control checks in Firebase Rules Playground or Emulator Suite: unauthenticated read/write denied; signed-in UID A can read/write A's data; UID A cannot read/write UID B; malformed metadata rejected. The app itself blocks a different local account/project to protect queued data.
- [ ] Password reset/sign-out/reauthentication with the same UID verified. No password or refresh token included in source/evidence.
- [x] Updated build installed and opened on the physical iPhone.
- [ ] Physical GPS/motion behavior checked in a walk. Simulator build is not a sensor test.
- [ ] Update docs/report-draft.md and regenerate report to state what really worked and what did not, including source failures or offline periods.
- [ ] Keep the demonstrable cloud dataset and account access available for the lecturer. Source ZIP contains README and all source/rules, no private exports or credentials.
- [ ] Blackboard: report first; source ZIP second; separate uploads.

## Evidence record (fill with actual results)

- Test date/time:
- Physical device/iOS:
- Firebase UID (redact in public versions):
- Own-data session IDs:
- Source vs server receipt timestamps / observed latency:
- Weather observation IDs and freshness:
- Offline replay outcome:
- Access-control test outcome:
- Known limitations:
