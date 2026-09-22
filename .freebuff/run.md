# NEURO_PREDICT_SYS — Run Doc

## Architecture

Two-tier architecture:

1. **Frontend** — Static Node.js server (port 3001 for preview, port 3000 for HTTPS)
2. **Backend** — FastAPI + uvicorn (port 8000) — optional, only needed for live ML predictions

### Frontend Design System

The new production UI lives in:
- `shared/design-system.css` — Tokens, typography, spacing, components, dark/light themes
- `shared/layout.css` — Adaptive shell: sidebar (desktop) → drawer + bottom nav (mobile)
- `shared/layout.js` — Theme, drawer, offline banner, page detection
- `shared/ui.js` — Toasts, escaping, safe DOM, formatting, dialogs
- `shared/auth.js` — Auth state (Clerk + JWT + auto-demo-login)
- `shared/api.js` — HTTP client with auth headers

### Pages Using New Design System
- `landing/index.html` — Public landing page (hero, features, how-it-works, CTA)
- `app/dashboard.html` — Clinical dashboard (KPIs, patients, activity, theaters)

### Pages Using Original Cyberpunk Style
- `ai_analysis/code.html` — AI Analysis (BrainLat + DARWIN)
- `prediction_command_center_v1/code.html` — Disease prediction vectors
- `final_diagnosis_report_v1/code.html` — Diagnosis reports
- `research_papers_1/code.html` — Research papers
- All other module pages

## How to Reproduce Artifacts

1. Copy `.env` from main checkout if needed
2. SSL certs: `certs/cert.pem` and `certs/key.pem` exist (self-signed, 365 days)
3. No build step — static files served directly

## How to Run

### HTTP (for preview)
```bash
HTTPS=false PORT=3001 node server.js
```

### HTTPS (local dev with self-signed certs)
```bash
PORT=3000 node server.js
# → https://127.0.0.1:3000/
```

### Backend (optional — for live ML predictions)
```bash
cd backend
set JWT_SECRET=your-secret
python app.py
# → http://127.0.0.1:8000
```

## Available Pages

| URL | Page | Design System |
|-----|------|---------------|
| `/` | Landing page | New (production) |
| `/app/dashboard.html` | Clinical dashboard | New (production) |
| `/ai_analysis/code.html` | AI Analysis | Original (cyberpunk) |
| `/prediction_command_center_v1/code.html` | Prediction Center | Original |
| `/final_diagnosis_report_v1/code.html` | Diagnosis Report | Original |
| `/research_papers_1/code.html` | Research Papers | Original |
| `/neural_archive_eeg_interpreter/code.html` | EEG Archive | Original |
| `/ot_scheduling_login/code.html` | OT Scheduling | Original |
| `/3fa_pharmacy_login/code.html` | Pharmacy | Original |
| `/pharmacist_login/code.html` | Pharmacist Portal | Original |
| `/neurosurgery_login/code.html` | Neurosurgery | Original |
| `/medical_history_login/code.html` | Medical History | Original |

## Current Preview

- **Port**: 3001 (HTTP)
- **Landing**: http://127.0.0.1:3001/
- **Dashboard**: http://127.0.0.1:3001/app/dashboard.html
