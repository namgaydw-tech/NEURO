# NEURO_PREDICT_SYS — Medical AI Disease Prediction Platform

> **Version 3.0.0** — Production-hardened healthcare research prototype

> ⚠️ **Disclaimer**: This is a research/prototype system. It has NOT been formally validated for clinical use. Do not falsely claim HIPAA, GDPR, or medical-device compliance. Formal compliance activities would still be required before clinical deployment.

---

## 📋 What Is This?

NEURO_PREDICT_SYS is an AI-powered neurological disease prediction platform that combines:

- **BrainLat ML Model** — Random Forest classifier (93.59% accuracy) trained on BrainLat EEG dataset for predicting Alzheimer's, Parkinson's, ALS, Epilepsy, MS, Brain Tumors, and Migraines
- **DARWIN Handwriting Analysis** — Secondary modality for handwriting-based neurological screening
- **Multi-module Medical Dashboard** — 12 interconnected modules covering diagnosis, pharmacy, surgery scheduling, research, and medical records
- **Real-time WebSocket Hub** — Inter-module communication for live updates across dashboard, analysis, and scheduling

---

## 📊 What Changed — Before vs After

### Phase 1: Initial Build (Commits 1-3)

| Feature | Status |
|---------|--------|
| FastAPI backend with in-memory DB | ✅ Working |
| ML model training pipeline (BrainLat dataset) | ✅ Working |
| DARWIN handwriting predictor | ✅ Working |
| 12 frontend modules (HTML/CSS/JS) | ✅ Working |
| PWA with service worker | ✅ Working |
| Node.js static server | ✅ Working |
| Pharmacy profile management | ✅ Working |
| OT scheduling with conflict detection | ✅ Working |
| Research paper browser | ✅ Working |
| Basic JWT auth | ⚠️ Functional but insecure |
| Demo accounts | ⚠️ Hardcoded, passwords exposed via API |
| RBAC | ❌ Not implemented |
| Refresh tokens | ❌ Not implemented |
| Rate limiting | ❌ Not implemented |
| Security headers | ❌ Not implemented |
| Mass assignment protection | ❌ Not implemented |
| Audit logging | ❌ Not implemented |
| Anti-hallucination middleware | ❌ Not implemented |
| WebSocket inter-module communication | ❌ Not implemented |
| Environment config validation | ❌ Hardcoded JWT secret |

### Phase 2: Playtest & Bug Fixes

| Fix | Issue | Resolution |
|-----|-------|------------|
| Login page crashes | `clerkMounted` undefined, missing `<form>` tag | Fixed `clerkMounted` → `window.clerkMounted`, added form wrapper |
| API 401 everywhere | No auto-login, demo mode unusable | Added auto-demo-login fallback in `shared/auth.js` |
| DARWIN button missing | Only in `NEURO/` copy, not root | Added DARWIN button HTML + JS to `ai_analysis/code.html` |
| Patient dropdown race | Loaded before auth token available | Added `await Auth.ready()` before API calls |
| Server.js clean URLs | `/ai_analysis` returning 404 | Added `.html` clean URL fallback in `server.js` |

### Phase 3: Production Security Hardening (Current)

| Security Fix | Severity | What Changed |
|--------------|----------|--------------|
| **Hardcoded JWT secret** | 🔴 Critical | Removed default `"neuro-predict-sys-dev-secret-key-change-in-prod"`. Config now refuses to boot in production without proper `JWT_SECRET`. Auto-generates for development. |
| **Demo-accounts password leak** | 🔴 Critical | `GET /auth/demo-accounts` no longer returns passwords. Returns emails and roles only. |
| **No RBAC** | 🟠 High | Added `require_role()` dependency to all 15 write endpoints. Demo users get 403 on patient creation, diagnosis, analysis, OT scheduling, pharmacy writes. |
| **Mass assignment** | 🟠 High | `update_diagnosis`, `update_slot`, `update_booking` now use typed Pydantic models (`DiagnosisUpdate`, `TimeSlotUpdate`, `BookingUpdate`) instead of raw `dict`. Profile update prevents non-admin users from setting `role`, `clearance_level`, `is_active`. |
| **No refresh tokens** | 🟠 High | Login/register now return `access_token` + `refresh_token` pair. `POST /auth/refresh` endpoint for rotation. |
| **No rate limiting** | 🟡 Medium | Login: 10/min, Register: 5/min per IP. Returns HTTP 429 with `Retry-After` header. |
| **No security headers** | 🟡 Medium | Added `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store` on API routes, `Strict-Transport-Security` in production. |
| **No audit logging** | 🟡 Medium | Audit events logged on: login success/failure, user registration, booking updates. In-memory store with database persistence hook. |
| **Anti-hallucination** | 🟡 Medium | POST/PUT request bodies scanned for proxy injection attacks (`ignore previous instructions`, `[INST]`, etc.). Blocked requests return 400 + broadcast to WebSocket dashboard. |
| **Secrets in git** | 🔴 Critical | `.env` files removed from git. `.gitignore` updated with comprehensive patterns for secrets, credentials, keys. |
| **WebSocket hub** | 🟢 New | Real-time inter-module communication: analysis → dashboard → scheduling. Heartbeat, auto-cleanup, event broadcasting. |
| **Config validation** | 🟡 Medium | `Settings.validate()` called at startup. Production blocks: weak JWT, wildcard CORS, demo data enabled. |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (PWA)                           │
│  HTML5 + Tailwind + Service Worker + Manifest                   │
│  Landing → Dashboard → AI Analysis → Prediction → Reports       │
│  Pharmacy Portal → OT Scheduling → Research → Medical History   │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                    NODE.JS STATIC SERVER                         │
│  Port 3001 (HTTP) / Port 3000 (HTTPS with self-signed certs)    │
│  Clean URL routing, static file serving                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP API + WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                  FASTAPI BACKEND (Port 8000)                     │
│                                                                  │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐    │
│  │ Security  │  │   WebSocket  │  │  Anti-Hallucination     │    │
│  │ Headers   │  │     Hub      │  │  Middleware              │    │
│  └──────────┘  └──────────────┘  └────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    CORE MODULES                           │   │
│  │  config.py │ auth.py │ database.py │ clerk.py            │   │
│  │  JWT + Refresh + RBAC │ InMemory/Supabase │ Rate Limit   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API ROUTES (48 endpoints)              │   │
│  │  Auth: register, login, demo-login, refresh, me, accounts│   │
│  │  Patients: CRUD with RBAC                                 │   │
│  │  Diagnoses: CRUD with RBAC                                │   │
│  │  Analysis: predict, get, by patient                       │   │
│  │  EEG: record, get, by patient                             │   │
│  │  Pharmacy: profile CRUD                                   │   │
│  │  OT: theaters, slots, bookings, daily-schedule            │   │
│  │  Research: list, get, create                              │   │
│  │  Medications: list, get, create (admin only)              │   │
│  │  Dashboard: stats, activity                               │   │
│  │  Users: profile get/update                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ML PIPELINE                             │   │
│  │  BrainLat Random Forest (93.59% accuracy)                 │   │
│  │  DARWIN Handwriting Predictor                              │   │
│  │  Rule-based fallback when no clinical data                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              DATABASE (Supabase PostgreSQL)                      │
│  In-Memory (demo) │ Supabase (production)                       │
│  Tables: users, patients, diagnoses, analyses, eeg_recordings,  │
│  research_papers, medications, ot_theaters, ot_slots,           │
│  ot_bookings, pharmacy_profiles                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication & Authorization

### Auth Flow

```
Login → JWT Access Token (30min) + Refresh Token (7 days)
         │
         ├── Access Token → Authorization: Bearer <token>
         │   Expires → 401 → Use Refresh Token
         │
         └── Refresh Token → POST /auth/refresh
             Returns new Access + Refresh pair
```

### RBAC Permission Matrix

| Role | Patients | Diagnoses | Analysis | EEG | Pharmacy | OT | Research | Admin |
|------|----------|-----------|----------|-----|----------|-----|----------|-------|
| **admin** | R/W/D | R/W | R/W | R/W | R/W | R/W/D | R/W | ✓ |
| **neurologist** | R/W | R/W | R/W | R/W | — | R | R | — |
| **surgeon** | R/W | R/W | R | — | — | R/W/D | R | — |
| **pharmacist** | R | — | — | — | R/W | — | — | — |
| **researcher** | R | — | R/W | R | — | — | R/W | — |
| **demo** | R | R | — | — | — | — | — | — |

### Key Security Features

- **JWT with JTI** — Every token has a unique ID for revocation
- **Refresh token rotation** — New pair issued on each refresh
- **Rate limiting** — Per-IP sliding window (login: 10/min, register: 5/min)
- **Mass assignment protection** — Typed Pydantic models, field whitelists
- **Audit logging** — Login, registration, booking changes tracked
- **Anti-hallucination** — Prompt injection blocked at middleware level
- **Security headers** — nosniff, DENY framing, XSS protection, no-cache on API

---

## 🧠 ML Models

### BrainLat Predictor (Primary)

| Metric | Value |
|--------|-------|
| Algorithm | Random Forest |
| Accuracy | 93.59% |
| F1 Score | 93.32% |
| Training Data | BrainLat EEG Dataset (Nature Scientific Data, 2023) |
| DOI | 10.1038/s41597-023-02806-8 |

**Supported Diseases:**
| Disease | Typical Confidence | Key Features |
|---------|-------------------|--------------|
| Alzheimer's Disease | 94.2% | memory_loss, confusion, disorientation |
| Parkinson's Disease | 91.8% | tremor, rigidity, bradykinesia |
| ALS | 87.1% | muscle_weakness, fasciculations |
| Epilepsy | 96.5% | seizures, staring_spells |
| Multiple Sclerosis | 88.3% | numbness, vision_problems |
| Brain Tumor | 85.4% | headache, seizures, personality_changes |
| Migraine | 93.1% | headache, nausea, light_sensitivity |

### DARWIN Predictor (Secondary)

Handwriting-based neurological screening using CSV input data.

### Training

```bash
cd backend
python -m ml.train_model
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### 1. Clone & Install

```bash
git clone https://github.com/namgaydw-tech/NEURO.git
cd NEURO

# Backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Frontend (no build needed — static HTML)
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values:
# JWT_SECRET=<generate: python -c "import secrets; print(secrets.token_hex(32))">
# SUPABASE_URL= (leave empty for demo mode)
# ENABLE_DEMO_DATA=true
```

### 3. Start Backend

```bash
cd backend
python start_server.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 4. Start Frontend

```bash
# From project root
node server.js
# Frontend: http://localhost:3001
```

### 5. Open in Browser

- **Landing Page**: http://localhost:3001/
- **Dashboard**: http://localhost:3001/app/dashboard.html
- **AI Analysis**: http://localhost:3001/ai_analysis/code.html
- **API Docs**: http://localhost:8000/docs

### Demo Accounts

| Email | Role | Password |
|-------|------|----------|
| admin@neuropredict.sys | admin | admin123 |
| neuro@neuropredict.sys | neurologist | neuro123 |
| pharma@neuropredict.sys | pharmacist | pharma123 |
| surgery@neuropredict.sys | surgeon | surgery123 |
| research@neuropredict.sys | researcher | research123 |
| demo@neuropredict.sys | demo | demo123 |

> ⚠️ Demo credentials are for development only. In production, `ENABLE_DEMO_DATA=false` disables them.

---

## 📁 Project Structure

```
NEURO/
├── backend/
│   ├── app.py                    # Main FastAPI app (WebSocket, middleware, routes)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Unified settings with production validation
│   │   ├── database.py           # Supabase + in-memory DB layer
│   │   ├── auth.py               # JWT, RBAC, rate limiting, audit logging
│   │   ├── clerk.py              # Clerk integration
│   │   ├── anti_hallucination.py # Input validation + hallucination detector
│   │   └── websocket.py          # Real-time inter-module hub
│   ├── routes.py                 # 48 API endpoints
│   ├── models.py                 # Pydantic request/response schemas
│   ├── ml/
│   │   ├── __init__.py           # Prediction engine
│   │   ├── train_model.py        # BrainLat training script
│   │   ├── darwin_predictor.py   # DARWIN handwriting predictor
│   │   └── models/               # Trained .pkl files
│   ├── seed.py                   # Demo data seeder
│   ├── supabase_schema.sql       # Production database schema
│   ├── requirements.txt          # Python dependencies
│   ├── start_server.py           # Launcher with env defaults
│   └── launch.py                 # Detached process launcher
├── ai_analysis/                  # AI Analysis page
├── prediction_command_center_v1/ # Prediction module
├── global_neural_dashboard_v1/   # Dashboard module
├── final_diagnosis_report_v1/    # Diagnosis report
├── research_papers_1/            # Research library
├── medical_history_archive/      # Medical records
├── medical_history_login/        # Login page
├── pharmacist_login/             # Login page
├── neurosurgery_login/           # Login page
├── 3fa_pharmacy_login/           # 3FA login page
├── app/
│   └── dashboard.html            # Production dashboard
├── landing/
│   └── index.html                # Landing page
├── shared/
│   ├── auth.js                   # Frontend auth client
│   ├── api.js                    # Frontend API client
│   ├── ui.js                     # UI components
│   ├── layout.js                 # Layout controller
│   ├── layout.css                # Responsive layout styles
│   └── design-system.css         # Design tokens + components
├── certs/                        # Self-signed SSL certs
├── server.js                     # Node.js static server (HTTP/HTTPS)
├── sw.js                         # Service worker (PWA)
├── manifest.json                 # PWA manifest
├── vercel.json                   # Vercel deployment config
├── capacitor.config.json         # Capacitor (Android/iOS) config
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

---

## 🌐 API Endpoints (48 total)

### Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | Rate limit | Create account (returns access + refresh) |
| POST | `/api/v1/auth/login` | Rate limit | Login (returns access + refresh) |
| GET | `/api/v1/auth/demo-login` | None (demo only) | Quick demo login |
| POST | `/api/v1/auth/refresh` | None | Exchange refresh for new token pair |
| GET | `/api/v1/auth/me` | Bearer | Current user info |
| GET | `/api/v1/auth/demo-accounts` | None | List demo accounts (no passwords) |

### Patients
| Method | Endpoint | RBAC | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/patients` | Any authenticated | List patients |
| GET | `/api/v1/patients/{id}` | Any authenticated | Get patient details |
| POST | `/api/v1/patients` | admin, neurologist, surgeon | Create patient |
| PUT | `/api/v1/patients/{id}` | admin, neurologist, surgeon | Update patient |
| DELETE | `/api/v1/patients/{id}` | admin only | Delete patient |

### Diagnoses
| Method | Endpoint | RBAC | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/diagnoses` | Any authenticated | List diagnoses |
| GET | `/api/v1/diagnoses/{id}` | Any authenticated | Get diagnosis |
| POST | `/api/v1/diagnoses` | admin, neurologist, surgeon | Create diagnosis |
| PUT | `/api/v1/diagnoses/{id}` | admin, neurologist, surgeon | Update (typed model) |

### AI Analysis
| Method | Endpoint | RBAC | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/analysis/predict` | admin, neurologist, researcher | Run ML prediction |
| GET | `/api/v1/analysis/{id}` | Any authenticated | Get analysis |
| GET | `/api/v1/analysis/patient/{id}` | Any authenticated | Patient analyses |

### EEG
| Method | Endpoint | RBAC | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/eeg/record` | admin, neurologist | Record EEG |
| GET | `/api/v1/eeg/{id}` | Any authenticated | Get recording |
| GET | `/api/v1/eeg/patient/{id}` | Any authenticated | Patient recordings |

### Pharmacy
| Method | Endpoint | RBAC | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/pharmacy/profile` | Any authenticated | Get profile |
| POST | `/api/v1/pharmacy/profile` | admin, pharmacist | Create profile |
| PUT | `/api/v1/pharmacy/profile/{id}` | admin, pharmacist | Update profile |

### OT Scheduling
| Method | Endpoint | RBAC | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/ot/theaters` | Any authenticated | List theaters |
| POST | `/api/v1/ot/theaters` | admin, surgeon | Create theater |
| GET | `/api/v1/ot/slots` | Any authenticated | List slots |
| POST | `/api/v1/ot/slots` | admin, surgeon | Create slot (conflict check) |
| PUT | `/api/v1/ot/slots/{id}` | admin, surgeon | Update slot (typed model) |
| POST | `/api/v1/ot/bookings` | admin, surgeon | Create booking |
| GET | `/api/v1/ot/bookings` | Any authenticated | List bookings |
| GET | `/api/v1/ot/bookings/{id}` | Any authenticated | Get booking |
| PUT | `/api/v1/ot/bookings/{id}` | admin, surgeon | Update booking (typed model) |
| DELETE | `/api/v1/ot/bookings/{id}` | admin, surgeon | Cancel booking |
| GET | `/api/v1/ot/daily-schedule` | Any authenticated | Full daily schedule |

### Research
| Method | Endpoint | RBAC | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/research` | Any authenticated | List papers |
| GET | `/api/v1/research/{id}` | Any authenticated | Get paper |
| POST | `/api/v1/research` | admin, researcher | Create paper |

### System
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | None | Health check |
| GET | `/api/v1/system/status` | None | System status |
| GET | `/api/v1/dashboard/stats` | Any authenticated | Dashboard statistics |
| GET | `/api/v1/dashboard/activity` | Any authenticated | Recent activity |

---

## 🔒 Environment Variables

```bash
# ── REQUIRED ─────────────────────────────────────────────
JWT_SECRET=          # Generate: python -c "import secrets; print(secrets.token_hex(32))"

# ── DATABASE ─────────────────────────────────────────────
SUPABASE_URL=        # Leave empty for in-memory demo mode
SUPABASE_ANON_KEY=   # Required if SUPABASE_URL set
SUPABASE_SERVICE_KEY= # Required if SUPABASE_URL set

# ── AUTH ─────────────────────────────────────────────────
CLERK_SECRET_KEY=    # Optional: Clerk integration
CLERK_PUBLISHABLE_KEY=
ENABLE_DEMO_DATA=true # Set false in production

# ── APP ──────────────────────────────────────────────────
APP_ENV=development  # development | staging | production
DEBUG=false
PORT=8000
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# ── SECURITY ─────────────────────────────────────────────
HALLUCINATION_CHECK=true
RATE_LIMIT_LOGIN=10  # per minute
RATE_LIMIT_API=120   # per minute
RATE_LIMIT_PREDICT=20 # per minute
AUDIT_ENABLED=true
```

---

## 🚢 Deployment

### Local Development

```bash
cd backend && python start_server.py   # Backend on :8000
node server.js                          # Frontend on :3001
```

### Vercel (Frontend + Serverless API)

```bash
npm i -g vercel
vercel --prod
# Set environment variables in Vercel dashboard
```

### Capacitor (Android/iOS)

```bash
npm install @capacitor/core @capacitor/cli
npx cap init "NEURO" "sys.neuropredict.app"
npx cap add android
npx cap add ios
npx cap sync
npx cap open android  # Opens Android Studio
npx cap open ios      # Opens Xcode
```

### Docker

```bash
docker build -t neuro-predict .
docker run -p 8000:8000 -e JWT_SECRET=your-secret neuro-predict
```

---

## 🧪 Testing

```bash
cd backend
pytest tests/ -v                    # Run all tests
pytest tests/test_auth.py -v        # Auth tests
pytest tests/test_rbac.py -v        # RBAC tests
pytest tests/test_rate_limit.py -v  # Rate limiting tests
```

---

## 📝 Secrets That Must Be Rotated

If this repository was previously public with real `.env` files committed:

1. **JWT_SECRET** — Generate new: `python -c "import secrets; print(secrets.token_hex(32))"`
2. **SUPABASE_SERVICE_KEY** — Rotate in Supabase dashboard
3. **CLERK_SECRET_KEY** — Rotate in Clerk dashboard
4. **All demo passwords** — Change before production use

---

## 📄 License

Research/Prototype — Not for clinical use without formal validation.
