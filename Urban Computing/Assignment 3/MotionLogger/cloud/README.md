# Firebase setup

This project uses Realtime Database and Email/Password Authentication only. There is no scheduled cloud function and no Firebase SDK dependency. Weather is collected on the phone while the app is open.

1. Select `urban-computing-a2` in Firebase Console.
2. Enable Authentication > Email/Password, and create your user in Authentication > Users.
3. In Realtime Database > Rules, paste all of `database.rules.json` and Publish.
4. Enter the supplied Belgium database URL and your app API key in the iPhone app, save settings, and sign in.
5. Verify both `users/<uid>/journeys` and `users/<uid>/weather/dublin-airport/observations` while the app is open.

Optional CLI deployment if Firebase CLI is already installed and signed in:

```sh
cd cloud
firebase deploy --only database --project urban-computing-a2
```

No CLI install or billing upgrade is required for the basic manual-console workflow. Firebase usage is still subject to your project's quotas. `.firebaserc` identifies the intended project. Do not set public read/write rules.
