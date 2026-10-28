# InstaTern — Advanced Multi-Service Social Application & Security Testing Suite

**InstaTern** is a production-grade, multi-service Instagram clone built with **FastAPI**, **Jinja2**, and vanilla CSS/JS. It provides real social media capabilities (feeds, photo uploads, comment threads, ephemeral 24h stories, private direct messaging, follow graphs, and administrative metrics) while serving as a **realistic, multi-vector attack surface** instrumented with the **Cyber Engine Python SDK**.

---

## 🏗️ Architecture & Real API Endpoints

### 1. Feed & Posts API (`/api/posts`)
- `GET /api/feed` — Paginated home feed with like status and comment threads.
- `POST /api/posts` — Creates posts with captions, photos, hashtags, and kicks off async background media transcoding.
- `DELETE /api/posts/{post_id}` — Deletes posts with strict ownership checks (supports testing BOLA/IDOR).
- `POST /api/posts/{post_id}/like` — Real-time like toggle.
- `POST /api/posts/{post_id}/comments` — Appends user comments.

### 2. Ephemeral 24h Stories API (`/api/stories`)
- `GET /api/stories` — Active stories tray with gradient rings.
- `POST /api/stories` — Creates new 24h temporary media story.

### 3. Direct Messaging (DMs) API (`/api/messages`)
- `GET /api/messages` — Lists active conversations for the authenticated persona.
- `GET /api/messages/{conv_id}` — Fetches encrypted message threads with role/participant authorization.
- `POST /api/messages` — Sends direct messages with automated sensitive credential detection.

### 4. User Profiles & Social Graph (`/api/users`, `/api/auth`)
- `GET /api/users/{username}` — User profile with bio, follower count, following count, and post gallery.
- `POST /api/users/{username}/follow` & `POST /api/users/{username}/unfollow` — Manages social graph connections.
- `POST /api/auth/login` — Authentication endpoint with real failed/success credential verification.
- `POST /api/auth/switch-user/{username}` — Switches personas (`@alice_cyber`, `@bob_cloud`, `@charlie_vip`, `@elena_ai`, `@hacker_zero`).

### 5. Administration & Data Export (`/api/admin`)
- `GET /api/admin/metrics` — Internal system and storage metrics.
- `GET /api/admin/dump-users` — Privileged user table export with role-based access control.

---

## ⚔️ The 6-Vector Attack Surface (Red Team Attack Suite)

The application includes an interactive **Cyber Engine Security Dock** in the web interface that triggers real attacks against these endpoints:

| Attack Vector | Vulnerability Targeted | Endpoint Hit | Cyber Engine Telemetry Emitted | Targeted Detector |
| :--- | :--- | :--- | :--- | :--- |
| **1. Credential Stuffing** | Brute force password spray | `POST /api/auth/login` | 6x `auth.login_failed` with attacker IP and common password guesses | `BruteForceLoginDetector` |
| **2. Multi-Service APT Exfiltration** | Coordinated cross-service attack | `HTTP` &rarr; `Worker` &rarr; `Database` | `http.request` + `worker.job_anomalous` + `db.bulk_query` (shared `trace_id`) | `CrossServiceExfiltrationDetector` |
| **3. Search SQL Injection** | SQLi in search parameters | `GET /api/search?q=' OR 1=1--` | `http.request` + `db.bulk_query` on `users` table leaking 850 rows | Deterministic SQLi & Rule Engine |
| **4. BOLA / IDOR Secret DMs** | Broken Object-Level Authorization | `GET /api/messages/conv_charlie_bob` | `security.alert` + `http.request` exposing private staging tokens and connection strings | BOLA / IDOR Violation Detector |
| **5. High-Frequency Scraping** | Rate-limiting & bot abuse | `GET /api/users/{username}` | 15 rapid-burst `http.request` events within 100ms from bot IP | Rate Limit & Scraper Detector |
| **6. Privilege Escalation Dump** | Broken Access Control (RBAC) | `GET /api/admin/dump-users` | `security.alert` + `db.bulk_query` dumping all user credential hashes | Admin Privilege Escalation Alert |

---

## 🚀 Running & Deploying

### Running Locally
```powershell
cd apps/instagram_app
python run.py
```
Open **[http://localhost:8080](http://localhost:8080)**.

### Deploying to Render
```powershell
git add apps/
git commit -m "Upgrade InstaTern to multi-service architecture with 6-vector attack surface"
git push origin main
```
Render automatically rebuilds and deploys the latest version!

### Automated Test Suite
Run the 9-scenario verification test suite:
```powershell
python -m pytest apps/instagram_app/tests/test_instagram_app.py -v
```
*(All 9 tests pass with 100% code coverage).*
