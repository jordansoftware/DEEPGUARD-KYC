<p align="center">
  <h1 align="center">🛡️ DeepGuard</h1>
  <p align="center"><strong>Open-source KYC & identity verification platform with forensic image analysis</strong></p>
  <p align="center">Detect deepfakes, forgeries, and document manipulation — self-hosted, no vendor lock-in.</p>
</p>

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/Get_Started-30_seconds-F43F5E?style=for-the-badge" alt="Get Started"></a>
  <a href="#live-demo"><img src="https://img.shields.io/badge/Live_Demo-Online-10B981?style=for-the-badge" alt="Live Demo"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="MIT License"></a>
  <a href="#star-history"><img src="https://img.shields.io/badge/Star_History-GitHub-FFD700?style=for-the-badge" alt="Star History"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white" alt="React 19">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white" alt="Docker">
</p>

---

## Why DeepGuard?

Existing KYC solutions (Jumio, Onfido, Sumsub) are:
- **Black-box** — you get a verdict, not *why*
- **Expensive** — $1-5+ per verification check
- **Cloud-only** — your users' IDs leave your infrastructure
- **Closed-source** — impossible to audit or customize

**DeepGuard is different:**

| | DeepGuard | Jumio / Onfido / Sumsub |
|---|---|---|
| **Forensic analysis** | MELA + ELA + Noise + EXIF + heatmap | Binary liveness only |
| **Transparency** | Per-signal scores + human-readable reasons | Black-box verdict |
| **Data stays local** | Self-hosted, your infrastructure | Data leaves to their cloud |
| **Pricing** | Free (compute cost only) | $1-5 per check |
| **License** | MIT, fork & modify | Proprietary |
| **Auditability** | Full source, explainable decisions | Impossible |

---

## Features

### 🔬 Forensic Image Analysis
Every uploaded image gets **4 independent forensic signals**:
- **MELA** (Multi-patch Error Level Analysis) — detects double-compression from image splicing
- **Noise Analysis** (PRNU approximation) — finds retouching, smoothing, or inserted elements
- **ELA** (Error Level Analysis) — pixel-level recompression divergence
- **EXIF Metadata** — flags editing software (Photoshop, GIMP) or AI generators (DALL-E, Midjourney)

Plus a **visual heatmap** showing exactly where anomalies were detected.

### 👤 Face Matching
Selfie ↔ ID photo comparison using DeepFace with 6 model options (VGG-Face, ArcFace, Facenet, etc.)

### 📄 OCR & Document Extraction
DocTR-powered OCR with MRZ parsing (TD1/TD3), field extraction, and document authenticity checks.

### 🛡️ AML/Sanctions Screening
Fuzzy name matching against sanctions lists (OFAC SDN, EU, PEP) using RapidFuzz.

### ⚖️ Decision Engine
Weighted scoring (forensic 50%, face 22%, OCR 18%, AML 10%) with defect penalties and SLA tracking.

### 🔴 Liveness Detection
Anti-spoofing analysis: eye shine, skin texture, facial symmetry, border artifacts — no model needed.

### 📹 Video Liveness
Short video analysis: micro-movements, blink patterns, temporal consistency — defeats static image replay.

### 📦 Batch Processing
Upload and process multiple documents in a single API call.

### 📊 Analytics Dashboard
Real-time metrics: case volumes, approval rates, SLA compliance, risk distribution, signal averages.

### 🔌 Integration Plugins
Slack, Telegram, Discord, Zapier — enable notifications with one click.

### ⚙️ Custom Rules Engine
Per-client configurable weights, penalties, and thresholds via API or dashboard.

### 📱 Mobile-Only Face Verification
End-to-face verification that **cannot** be faked on a desktop:
- Dashboard generates a QR code via `POST /api/kyc/cases/{id}/face-session`
- Applicant scans it on their phone → opens `/mobile/verify?token=...`
- Camera capture with **anti-emulator** + **anti-bot** heuristics
- Backend runs face match + liveness → updates the case
- The QR session token is **single-use** and **JWT-signed** (aud/iss/exp)
- The admin dashboard only **displays the result** — it never initiates the flow

### 🔑 Multi-Tenant API Keys
- Each client gets a **SHA-256 hashed** API key (`dg_...`), returned once on create
- Per-client **quota** + **usage tracking**
- **Key rotation** endpoint
- **Revoke / delete** lifecycle (inactive keys can be hard-deleted)

### 🔔 Signed Webhooks
- Outgoing webhook deliveries are signed **HMAC-SHA256** (`X-DeepGuard-Signature`)
- `POST /api/webhooks/{id}/test` for dry-runs
- SSRF protection (private/loopback IPs blocked)

### 🔔 Real-time Updates
WebSocket notifications for case status changes.

### 📧 Email Notifications
SMTP-based alerts for case completion, SLA warnings, and review requests.

---

## How It Works

```
 Your App                     DeepGuard SaaS (self-hosted)              End User
    │                              │                                        │
    │ 1. Clone + run (Docker)     │                                        │
    ├─────────────────────────────►                                        │
    │                              │                                        │
    │ 2. Generate API key          │                                        │
    ├─────────────────────────────►  /api/clients                           │
    │◄───────────────────────────────  { api_key: "dg_xxx" }               │
    │                              │                                        │
    │ 3. Submit ID document        │                                        │
    ├─────────────────────────────►  /api/kyc/cases (multipart)            │
    │                              │  ┌──────────────────────────────┐     │
    │                              │  │ Forensic engine              │     │
    │                              │  │  MELA + ELA + Noise + EXIF  │     │
    │                              │  │  + heatmap overlay           │     │
    │                              │  ├──────────────────────────────┤     │
    │                              │  │ OCR (DocTR) + MRZ parsing    │     │
    │                              │  ├──────────────────────────────┤     │
    │                              │  │ Face match (DeepFace)        │     │
    │                              │  ├──────────────────────────────┤     │
    │                              │  │ AML / sanctions screening    │     │
    │                              │  ├──────────────────────────────┤     │
    │                              │  │ Decision engine (weighted)   │     │
    │                              │  └──────────────────────────────┘     │
    │◄───────────────────────────────  { verdict, score, signals }         │
    │                              │                                        │
    │ 4. Trigger face verification   /api/kyc/cases/{id}/face-session     │
    ├─────────────────────────────►                                        │
    │                              │◄─────────────────────────────────────  │
    │                              │  QR code shown in your UI              │
    │                              │                                        │
    │                              │         5. Scan QR → /mobile/verify    │
    │                              │◄────────────────────────────────────── │
    │                              │  Face match + liveness + device check │
    │◄──────────────────────────────  webhook: case.completed (signed)     │
```

The admin dashboard is **read-only** for face verification: it shows the result,
never initiates the flow. The caller app (you) triggers step 4 and displays the
QR code to your user.

---

## Quick Start

### Option 1: Docker (recommended)

```bash
git clone https://github.com/jordansoftware/deepguard.git
cd deepguard
docker compose up -d
```

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:3000 |
| **API Docs** | http://localhost:8765/docs |
| **Health** | http://localhost:8765/api/health |

### Option 2: Manual setup

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8765 --reload
```

**Dashboard:**
```bash
cd dashboard
npm install
npm run dev
```

### Verify it works

```bash
curl http://localhost:8765/api/health
# → {"status":"ok"}

curl http://localhost:8765/api/kyc/cases -H "X-API-Key: dg_demo" | python3 -m json.tool
# → 8 seed cases with scores, verdicts, and heatmaps
```

> The seeded demo client uses the API key `dg_demo`. Generate your own from
> **Settings → API Keys** in the dashboard for production.

---

## Security

- **API key auth** — every request requires `X-API-Key` (SHA-256 hashed in DB)
- **Rate limiting** — `slowapi` per-endpoint limits (e.g. 20/minute on `/analyze`)
- **SSRF protection** — webhook URLs are validated against private/loopback ranges
- **XSS** — all API responses are JSON; webhooks sign payloads with HMAC-SHA256
- **SQL injection** — SQLAlchemy 2.0 parameterized queries; no raw SQL
- **Secrets masking** — plugin configs mask secrets in dashboard responses
- **CORS** — restricted to configured origins (`CORS_ORIGINS`)
- **Mobile anti-emulator** — device heuristics + advisory verdicts (never "trusted" from client signals alone)

---

## Integration

DeepGuard can be integrated into your project in 3 ways:

### 1. Microservice (HTTP API)

The simplest integration. DeepGuard runs as a separate service, your app calls it via HTTP.

```python
import httpx

# Analyze a document
with open("id_card.jpg", "rb") as f:
    r = httpx.post("http://deepguard:8765/api/analyze", files={"file": f})
result = r.json()
print(result["verdict"], result["score"])
```

```javascript
// React / Next.js
const formData = new FormData()
formData.append('file', file)
const res = await fetch('http://localhost:8765/api/analyze', {
  method: 'POST',
  body: formData,
})
const result = await res.json()
```

### 2. Python Package

Import directly in your Python code:

```bash
cd backend && pip install -e .
```

```python
from deepguard import analyze_image, match_faces, detect_liveness

# Forensic analysis
result = analyze_image("id_card.jpg")
print(result["verdict"], result["score"])

# Face matching
match = match_faces("selfie.jpg", "id_photo.jpg")
print(match["match"], match["distance"])

# Liveness detection
live = detect_liveness("face.jpg")
print(live["is_live"], live["score"])
```

```bash
# Or use the CLI
python -m deepguard analyze image.jpg
python -m deepguard match selfie.jpg id.jpg
python -m deepguard liveness face.jpg
python -m deepguard ocr document.jpg
python -m deepguard serve --port 8765
```

### 3. React Components

Drop-in React components for your frontend:

```bash
cd packages/react && npm install
```

```tsx
import { DeepGuardProvider, AnalysisUploader, FaceMatcher, LivenessCheck } from '@deepguard/react'

function App() {
  return (
    <DeepGuardProvider config={{ apiUrl: 'http://localhost:8765' }}>
      <AnalysisUploader onResult={(r) => console.log(r.verdict)} />
      <FaceMatcher onResult={(r) => console.log(r.match)} />
      <LivenessCheck onResult={(r) => console.log(r.is_live)} />
    </DeepGuardProvider>
  )
}
```

---

## Architecture

```
deepguard/
├── backend/                  # FastAPI (Python 3.12)
│   ├── deepguard/            # Python package (pip install -e .)
│   │   ├── __init__.py       # Public API: analyze_image, match_faces, etc.
│   │   ├── __main__.py       # CLI: python -m deepguard
│   │   ├── api.py            # FastAPI microservice
│   │   ├── core.py           # Forensic analysis wrapper
│   │   ├── face.py           # Face matching wrapper
│   │   ├── ocr.py            # OCR/MRZ wrapper
│   │   ├── liveness.py       # Liveness detection wrapper
│   │   ├── address.py        # Address verification wrapper
│   │   └── decision.py       # Decision engine wrapper
│   ├── app/                  # Backend internals
│   │   ├── routers/          # 30 API endpoints
│   │   ├── services/         # AI engines (OCR, face, liveness)
│   │   ├── signals.py        # Forensic engine (MELA, ELA, Noise, EXIF)
│   │   └── workflow.py       # Decision engine
│   ├── pyproject.toml        # Python package config
│   ├── Dockerfile
│   └── requirements.txt
├── dashboard/                # Vite + React 19 + TanStack Router
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
├── packages/
│   └── react/                # @deepguard/react component library
│       ├── src/
│       │   ├── index.ts
│       │   ├── provider.tsx
│       │   ├── analysis-uploader.tsx
│       │   ├── face-matcher.tsx
│       │   ├── liveness-check.tsx
│       │   └── results-table.tsx
│       └── package.json
├── docker-compose.yml
└── README.md
```

---

## API Reference

**Base URL:** `http://localhost:8765`

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analyze` | Forensic image analysis |
| `POST` | `/api/kyc/cases` | Submit document for KYC |
| `GET` | `/api/kyc/cases` | List all cases |
| `GET` | `/api/kyc/cases/{id}` | Case detail |
| `POST` | `/api/kyc/cases/{id}/decision` | Approve/reject case |

### Batch Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/batch/upload` | Upload multiple files |
| `GET` | `/api/batch/{id}` | Batch job status |
| `GET` | `/api/batch/` | List all batch jobs |

### Analytics & Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/analytics/overview` | High-level metrics |
| `GET` | `/api/analytics/trends` | Daily trends |
| `GET` | `/api/analytics/risk-distribution` | Score distribution |
| `GET` | `/api/analytics/sla-compliance` | SLA metrics |
| `GET` | `/api/export/cases` | Export CSV/Excel |

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/rules/defaults` | Default rules |
| `GET/PUT` | `/api/rules/client/{id}` | Per-client rules |
| `GET/PUT` | `/api/plugins/{name}` | Plugin config |
| `POST` | `/api/plugins/{name}/test` | Test plugin |

### Client Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/clients` | Create client |
| `GET` | `/api/clients` | List clients |
| `POST` | `/api/clients/{id}/rotate-key` | Rotate API key |

### Webhooks & Screening

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/screening/aml` | AML/sanctions check |
| `POST` | `/api/webhooks` | Create webhook |
| `POST` | `/api/webhooks/{id}/test` | Test webhook |
| `GET` | `/api/reports/{case_id}` | PDF report |

### Mobile Face Verification

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/kyc/cases/{id}/face-session` | Create QR + JWT session |
| `GET` | `/api/mobile/status/{token}` | Poll session status |
| `POST` | `/api/mobile/verify` | Mobile submits selfie + liveness |

---

## Example: Analyze a Document

```bash
curl -X POST http://localhost:8765/api/analyze \
  -F "file=@id_card.jpg"
```

**Response:**
```json
{
  "score": 72,
  "verdict": "suspect",
  "verdict_label": "Suspect",
  "heatmap": "data:image/png;base64,...",
  "signals": {
    "mela": {"score": 65, "note": "12% of surface shows abnormal compression benefit"},
    "noise": {"score": 30, "note": "Homogeneous residual noise"},
    "ela": {"score": 45, "note": "Localized compression divergences"},
    "meta": {"score": 20, "notes": ["No EXIF metadata"]}
  },
  "reasons": ["12% of surface shows abnormal compression benefit (content likely re-inserted)"]
}
```

---

## Decision Engine

The scoring pipeline combines 4 signal domains:

```
Score = Σ(signal × weight) - defect_penalties

Weights:
  Forensic (MELA+ELA+Noise+EXIF)  50%
  Face Match                       22%
  OCR/MRZ                          18%
  AML/Sanctions                    10%

Verdicts:
  AML hit      → Rejected (immediate block)
  Score > 88   → Approved
  Score 55-88  → Under Review (manual)
  Score < 55   → Rejected
  Score < 15   → Unknown
```

**Defect penalties** (subtracted from score):
| Defect | Penalty |
|--------|---------|
| Document expired | -5 |
| AML match | -4 |
| Face mismatch | -3 |
| MRZ inconsistent | -3 |
| Liveness failed | -3 |
| Doc type mismatch | -2 |
| MRZ missing | -2 |
| Address mismatch | -2 |

---

## Configuration

All settings are configurable via environment variables:

```bash
# Database
DATABASE_URL=sqlite:///data/deepguard.db

# AI Engines
ENABLE_OCR=true
ENABLE_FACEMATCH=true
ENABLE_LIVENESS=true
ENABLE_VIDEO_LIVENESS=true
ENABLE_ADDRESS_VERIFY=true
FACE_MATCH_THRESHOLD=0.40

# Workflow
DEFAULT_SLA_HOURS=48
AUTO_REJECT_SCORE=70
AUTO_APPROVE_SCORE=15

# Email (optional)
EMAIL_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=your-app-password

# Security
DEEP_GUARD_SECRET_KEY=change-me-in-production
DEEP_GUARD_ALLOW_ANON=true  # sandbox mode
```

---

## Tech Stack

**Backend:**
- Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic
- DocTR (OCR) · DeepFace (face matching) · Pillow + NumPy (forensics)
- RapidFuzz (AML screening) · ReportLab (PDF reports)

**Dashboard:**
- Vite 8 · React 19 · TypeScript
- TanStack Router + TanStack Query + TanStack Table
- shadcn/ui (Radix + Tailwind CSS 4)
- Zustand (state) · Sonner (toasts)

**Infrastructure:**
- Docker + Docker Compose
- SQLite (default) · PostgreSQL (supported)
- WebSocket (real-time updates)

---

## Contributing

Contributions welcome! Please open an issue first to discuss what you'd like to change.

```bash
git clone https://github.com/jordansoftware/deepguard.git
cd deepguard
docker compose up -d
# Make changes, then:
# Backend: run tests with pytest
# Dashboard: npm run lint
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Star History

If you find DeepGuard useful, please give it a ⭐ on GitHub. It helps others discover the project.

<p align="center">
  <a href="https://star-history.com/#jordansoftware/deepguard&Date">
    <img src="https://api.star-history.com/svg?repos=jordansoftware/deepguard&type=Date" alt="Star History Chart" width="600">
  </a>
</p>

---

<p align="center">
  Built with ❤️ for a more transparent identity verification ecosystem.
</p>
