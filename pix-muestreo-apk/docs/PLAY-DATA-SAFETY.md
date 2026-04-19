# Play Store — Data Safety form answers

Copy these answers into **Play Console → App content → Data safety**.
Keep the source of truth here so we don't drift between Console and reality.

## Section 1 — Data collection and security

> **Does your app collect or share any of the required user data types?**
→ **Yes**

> **Is all of the user data collected by your app encrypted in transit?**
→ **Yes** — Network Security Config enforces HTTPS + TLS 1.2+ for every non-`localhost`
  destination; cleartext traffic is blocked.

> **Do you provide a way for users to request that their data is deleted?**
→ **Yes** — In-app "Eliminar mi cuenta" + e-mail `privacidad@pixadvisor.network`.

---

## Section 2 — Data types collected

| Data type | Collected | Shared | Optional | Ephemeral | Why |
|---|---|---|---|---|---|
| **Location → Approximate location** | ❌ | ❌ | — | — | We always use precise. |
| **Location → Precise location** | ✅ | ❌ | ✅ | ❌ | Georeferenciar muestras. In-app functionality. |
| **Personal info → Name** | ✅ | ❌ | ❌ | ❌ | Account management. |
| **Personal info → Email address** | ✅ | ❌ | ❌ | ❌ | Login / account. |
| **Personal info → User IDs** | ✅ | ✅ (Supabase) | ❌ | ❌ | Authentication. |
| **Personal info → Address** | ❌ | ❌ | — | — | — |
| **Personal info → Phone number** | ❌ | ❌ | — | — | — |
| **Personal info → Race/ethnicity, Politics, Religion, Sexual orientation** | ❌ | ❌ | — | — | — |
| **Financial info (any)** | ❌ | ❌ | — | — | No in-app purchases. |
| **Health & fitness (any)** | ❌ | ❌ | — | — | — |
| **Messages → Email / SMS / Other** | ❌ | ❌ | — | — | — |
| **Photos and videos → Photos** | ✅ | ❌ | ✅ | ❌ | Foto de la muestra / plaga. |
| **Photos and videos → Videos** | ❌ | ❌ | — | — | — |
| **Audio files → Voice or sound recordings** | ❌ | ❌ | — | — | Voice assistant is client-side only; nothing persisted. |
| **Audio files → Music files, Other audio** | ❌ | ❌ | — | — | — |
| **Files and docs → Files and docs** | ✅ | ✅ (Supabase, Drive opt-in) | ❌ | ❌ | Reports, KMZ, GeoJSON. |
| **Calendar → Calendar events** | ❌ | ❌ | — | — | — |
| **Contacts → Contacts** | ❌ | ❌ | — | — | — |
| **App activity → App interactions** | ✅ | ❌ | ✅ | ❌ | Breadcrumbs for crash reports (opt-in). |
| **App activity → In-app search history** | ❌ | ❌ | — | — | — |
| **App activity → Installed apps** | ❌ | ❌ | — | — | — |
| **App activity → Other user-generated content** | ✅ | ✅ (Supabase) | ❌ | ❌ | Sample data (pH, EC, notes). |
| **App activity → Other actions** | ❌ | ❌ | — | — | — |
| **Web browsing → Web browsing history** | ❌ | ❌ | — | — | — |
| **App info and performance → Crash logs** | ✅ | ✅ (Sentry, opt-in) | ✅ | ❌ | Fix bugs. |
| **App info and performance → Diagnostics** | ✅ | ✅ (Sentry, opt-in) | ✅ | ❌ | Performance troubleshooting. |
| **App info and performance → Other app performance data** | ❌ | ❌ | — | — | — |
| **Device or other IDs** | ✅ | ✅ (Google Play Integrity) | ❌ | ✅ | Device attestation only — no persistent ID shared. |

---

## Section 3 — Data usage & handling per data type

For each row marked collected above, Play Console asks **why** (purpose) and
**how** (processed on device vs. server).

### Precise location
- **Purposes:** App functionality.
- **Shared with third parties?** No.
- **Processing:** Mainly on device; encrypted in transit when synced.
- **Optional?** Yes — user can deny the location permission; app will
  disable the "take sample" button but keep working for review/export.

### Name
- **Purposes:** Account management.
- **Shared?** No.
- **Processing:** Collected during onboarding by the account admin.

### Email address
- **Purposes:** Account management, Developer communications.
- **Shared?** No.
- **Processing:** Authentication via Supabase.

### User IDs
- **Purposes:** Account management, Analytics.
- **Shared with:** Supabase (database-as-a-service).
- **Processing:** Stored server-side to implement RLS.

### Photos
- **Purposes:** App functionality.
- **Shared?** No by default. User can opt-in to Google Drive backup.
- **Processing:** Compressed on device, stored server-side (Supabase).

### Files and docs
- **Purposes:** App functionality.
- **Shared with:** Supabase, Google Drive (opt-in).
- **Processing:** Reports (PDF/HTML), KMZ lots, GeoJSON boundaries.

### App interactions / Other user-generated content
- **Purposes:** App functionality.
- **Shared with:** Supabase.
- **Processing:** Sample observations, measurements, technician notes.

### Crash logs / Diagnostics
- **Purposes:** Analytics (troubleshooting).
- **Shared with:** Sentry.
- **Processing:** Anonymized (hashed user ID, no email/location/PII).
- **Optional:** **Yes** — Ajustes → Privacidad → Desactivar telemetría.

### Device or other IDs (Play Integrity)
- **Purposes:** Fraud prevention, security, and compliance.
- **Shared with:** Google (Play Integrity service).
- **Processing:** Ephemeral attestation token; not stored client-side.

---

## Section 4 — Security practices

- **Data encrypted in transit:** Yes (HTTPS/TLS 1.2+).
- **Data encrypted at rest:** Yes (Supabase server-side + AES-GCM 256 on device IndexedDB).
- **Follows Play Families Policy:** Not applicable (app is B2B, not for children).
- **Independent security review:** No (self-audited against OWASP MASVS Level 1 internally).
- **Data deletion:** Users can request deletion in-app and via `privacidad@pixadvisor.network`.

---

## Section 5 — Privacy policy

**URL:** https://pixadvisor.network/privacy-policy — serve `docs/privacy-policy.html`
from the web server; make sure it's reachable without login.
