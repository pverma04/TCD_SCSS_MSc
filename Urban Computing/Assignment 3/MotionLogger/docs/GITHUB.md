# Publishing the source safely

The app asks for the Firebase Web API key on the phone. It saves configuration in iOS UserDefaults, not in a source file. The Firebase password is used only for sign-in; its session refresh token is stored in iOS Keychain. Neither the password nor session tokens are included in the project or source ZIP.

The supplied .gitignore excludes GoogleService-Info.plist, local .env files, service-account credential filenames, signing keys/profiles, SQLite databases and personal CSV/GPX exports. Do not rename credentials to bypass these patterns. Existing tracked files are not made untracked by a new ignore rule.

Before pushing, review:

```sh
git status --short
git diff --cached --name-only
```

If a sensitive file is already tracked, remove it from the index while keeping the local copy, using its exact path:

```sh
git rm --cached -- path/to/credential-file
```

If an actual password, session token or service-account private key has already been pushed, removing the file in a later commit does not remove the secret from history. Revoke/rotate the exposed credential, then address Git history as appropriate.

The project ID, database URL, bundle ID and security rules are safe to publish. A Firebase API key restricted to Firebase services is app configuration rather than database authorization, but this project keeps your chosen key out of source anyway. Database rules must remain private-by-UID; hiding the URL or API key is not a substitute for access control.

Firebase guidance: https://firebase.google.com/docs/projects/api-keys
