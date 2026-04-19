# Play Integrity — server-side verification

The client (`js/integrity.js`) requests an integrity token and sends it to a
backend endpoint for verification against Google's Play Integrity verdict API.
**Until the server side is wired up, the client fails open** — no legitimate
user is blocked, but the gate also provides no real protection.

## Backend contract

Both endpoints live in Supabase Edge Functions under
`supabase/functions/integrity-*`.

### `POST /functions/v1/integrity-nonce`
- Auth: user's Bearer JWT (same as other API calls).
- Returns: `{ "nonce": "<urlsafe-b64 ≥ 16 bytes>" }`.
- Stores `{ user_id, nonce, created_at }` in a short-lived table
  (`integrity_nonces`, TTL 5 min, RLS = user can only see their own).

### `POST /functions/v1/integrity-verify`
- Auth: user's Bearer JWT.
- Body: `{ "nonce": "...", "token": "..." }`.
- Flow:
  1. Verify `nonce` exists in `integrity_nonces` for this user and hasn't expired.
  2. Delete the nonce row (one-shot use).
  3. POST the `token` to `https://playintegrity.googleapis.com/v1/PKG:decodeIntegrityToken`
     with a service-account credential scoped to the Cloud project.
  4. Inspect the JSON verdict:
     - `deviceIntegrity.deviceRecognitionVerdict` must contain either
       `MEETS_DEVICE_INTEGRITY` (hard pass) or `MEETS_BASIC_INTEGRITY` (warn).
     - `appIntegrity.appRecognitionVerdict` must be `PLAY_RECOGNIZED`.
     - `accountDetails.appLicensingVerdict` should be `LICENSED`.
  5. Return `{ "verdict": "pass" | "warn" | "fail", "reason": "..." }`.

## Configuration

1. Play Console → **App Integrity** → **Integrity API**. Copy the
   **Cloud project number** (not ID — the numeric one).
2. Open `app/src/main/res/values/strings.xml`. Replace the placeholder
   `<string name="integrity_cloud_project">0</string>` with the real number.
3. In Google Cloud Console → same project → create a service account with the
   role **Play Integrity API → Play Integrity verifier**. Download the JSON key.
4. Store the key in Supabase Vault (`integrity_sa_json`). The Edge Function
   reads it at cold-start and uses it to sign the `decodeIntegrityToken` call.

## Rollout strategy

- **Week 1:** Deploy server-side in **warn-only** mode: log every `fail`
  verdict with the device info + user, but return `pass` to the client.
  Observe the false-positive rate.
- **Week 2:** Promote to **soft-block** — on `fail`, require a second-factor
  (OTP to e-mail) before allowing the sensitive operation, but don't lock the
  account outright.
- **Week 3+:** Promote to **hard-block** only for the master-key login and
  "delete project" flows. Regular sample-collection stays in warn-only forever.

Never hard-block regular colecta flows on Integrity — technicians work in
remote fields on donated/used Android devices where the verdict is often
`MEETS_BASIC_INTEGRITY` only. Blocking them means no samples that day.
