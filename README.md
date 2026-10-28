# InstaTern — Instagram Test Application for Cyber Engine

**InstaTern** is a standalone, full-featured Instagram-like social media application built with **FastAPI**, **Jinja2**, and vanilla CSS/JS. It is pre-instrumented with the **Cyber Engine Python SDK** to stream realistic application telemetry (`http.request`, `auth.login_failed`, `db.bulk_query`, `worker.job_anomalous`) directly to Cyber Engine for continuous threat detection and AI-assisted deep investigation.

---

## 🌟 Features

- **Instagram UI & Experience**:
  - Stories tray with glowing gradient rings (`@alice_cyber`, `@bob_cloud`, `@elena_ai`, `@charlie_vip`).
  - Feed with photos, captions, expandable `#tags`, like heart toggles, and live comments.
  - Explore & Search bar with interactive SQL injection testing.
  - Modal dialog for creating new posts with thumbnail processing.
  - Multi-user account switcher for testing different personas.
- **Cyber Engine Telemetry & Attack Testing Dock**:
  - Built-in floating sidebar console displaying real-time connectivity to Cyber Engine (`STREAMING / 200 OK`).
  - **One-Click Attack Generators**:
    1. ⚡ **Brute Force Spray**: Rapidly fires 6 failed login attempts against `@charlie_vip` &rarr; triggers Cyber Engine's `BruteForceLoginDetector`.
    2. 🚨 **APT Exfiltration Sequence**: Coordinated multi-service attack (API Gateway &rarr; Worker Decompression Anomaly &rarr; Sensitive Database Bulk Exfiltration) with shared `trace_id` &rarr; triggers `CrossServiceExfiltrationDetector`.
    3. 🔍 **Search SQL Injection**: Injects `' OR 1=1; SELECT * FROM users --` leaking 850 user records &rarr; emits `db.bulk_query`.
    4. ✅ **Benign Traffic Simulation**: Generates legitimate browsing, liking, and commenting telemetry with zero false positives.
  - **Live Telemetry Stream**: Rolling feed showing recently emitted events, target resources, correlated trace IDs, and Cyber Engine acceptance latencies.

---

## 🚀 Running Locally

### 1. Install Dependencies
```bash
cd apps/instagram_app
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default settings point to `http://localhost:8000` (local Cyber Engine):
```env
PORT=8080
CYBER_ENGINE_URL=http://localhost:8000
CYBER_ENGINE_API_KEY=ce_live_test_api_key_secret_12345
TENANT_ID=tenant-alpha
APP_ID=instagram-app
SERVICE_ID=instagram-api
```

### 3. Launch the Application
```bash
python run.py
```
Open your browser at **[http://localhost:8080](http://localhost:8080)**.

---

## ☁️ Deploying to the Cloud

The application is containerized with dynamic port binding (`$PORT`), making it compatible with all major cloud container platforms.

### Option A: Google Cloud Run (Recommended)

1. Build and deploy directly with Google Cloud SDK:
```bash
cd apps/instagram_app

# Deploy to Cloud Run
gcloud run deploy instatern-app \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CYBER_ENGINE_URL="https://<your-cloud-cyber-engine-url>",CYBER_ENGINE_API_KEY="<your-api-key>",TENANT_ID="tenant-alpha",APP_ID="instagram-app"
```

2. Cloud Run will output your live URL (e.g., `https://instatern-app-xyz.a.run.app`).

### Option B: Docker

Build and run the container locally or on any cloud VM:
```bash
docker build -t instatern-app .
docker run -p 8080:8080 \
  -e CYBER_ENGINE_URL="https://<your-cyber-engine-url>" \
  -e CYBER_ENGINE_API_KEY="<your-api-key>" \
  instatern-app
```

### Option C: Docker Compose (Instagram App + Cyber Engine Together)

To spin up both Cyber Engine and the Instagram test app together:
```bash
docker compose -f apps/instagram_app/docker-compose.yml up --build
```

---

## 📡 API Endpoints

| Method | Endpoint | Description | Cyber Engine Telemetry Emitted |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Health & Cyber Engine status check | — |
| `GET` | `/api/feed` | Retrieve post feed | `http.request` |
| `POST` | `/api/posts` | Create new post | `http.request`, `db.query` |
| `POST` | `/api/posts/{id}/like` | Toggle like on post | `http.request` |
| `POST` | `/api/posts/{id}/comments` | Add comment | `http.request` |
| `POST` | `/api/auth/login` | User login | `auth.login_success` or `auth.login_failed` |
| `GET` | `/api/search?q=...` | Search users/posts | `http.request` + `db.bulk_query` (on SQLi) |
| `POST` | `/api/worker/process-media` | Async thumbnail worker | `worker.job_completed` or `worker.job_anomalous` |
| `POST` | `/api/attacks/brute-force` | Simulates 6 failed logins | 6x `auth.login_failed` |
| `POST` | `/api/attacks/cross-service-exfil` | Simulates multi-service APT | `http` + `worker` + `db.bulk_query` |
| `POST` | `/api/attacks/benign-traffic` | Simulates normal user browsing | Normal telemetry |
| `GET` | `/api/attacks/recent-telemetry` | Rolling buffer of sent events | — |
| `GET` | `/api/attacks/status` | Engine connectivity details | — |

---

## 🧪 Automated Verification

Run the test suite to ensure all endpoints, models, and attack simulations work:
```bash
pytest apps/instagram_app/tests/test_instagram_app.py -v
```
All 7 tests verify health, social workflows, attack triggers, and telemetry emission.

"# InstaTern-TERNLINE-" 
