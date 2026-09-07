# NEURO_PREDICT_SYS — Run Documentation

## Architecture

- **Frontend**: Pure HTML + Tailwind CSS (CDN) — standalone `code.html` files per module
- **Backend**: Python FastAPI with in-memory demo mode (or Supabase for production)
- **ML Engine**: scikit-learn prediction engine (demo mode when no trained model)

## How to Run

### Backend API Server (Port 8000)

```bash
# From project root
cd backend
../backend/venv/Scripts/python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Static Server (Port 3001)

```bash
# From project root — uses npx serve
npx serve -l 3001 -C .
```

### Access

- **Frontend Hub**: http://127.0.0.1:3001/
- **Backend API**: http://127.0.0.1:8000/api/v1
- **API Docs (Swagger)**: http://127.0.0.1:8000/docs

## Demo Accounts

| Email | Password | Role |
|-------|----------|------|
| admin@neuropredict.sys | admin123 | Admin |
| neuro@neuropredict.sys | neuro123 | Neurologist |
| pharma@neuropredict.sys | pharma123 | Pharmacist |
| surgery@neuropredict.sys | surgery123 | Surgeon |
| research@neuropredict.sys | research123 | Researcher |
| demo@neuropredict.sys | demo123 | Demo User |

## Environment Setup

### Reproduce Artifacts (Fresh Checkout)
1. Create Python venv: `py.exe -m venv backend/venv`
2. Install deps: `backend/venv/Scripts/pip.exe install -r backend/requirements.txt`
3. Downgrade bcrypt: `backend/venv/Scripts/pip.exe install "bcrypt==4.0.1"`
4. Copy `.env` from main checkout (or create from `.env.example`)

### Production (Supabase)
1. Create Supabase project at https://supabase.com
2. Run `backend/supabase_schema.sql` in SQL Editor
3. Set `SUPABASE_URL` and `SUPABASE_KEY` in `.env`

## Backend API Endpoints

- `POST /api/v1/auth/login` — Login with email/password
- `POST /api/v1/auth/register` — Register new user
- `GET /api/v1/auth/demo-accounts` — List demo accounts
- `GET /api/v1/patients` — List patients (paginated)
- `POST /api/v1/patients` — Create patient
- `GET /api/v1/diagnoses` — List diagnoses
- `POST /api/v1/diagnoses` — Create diagnosis
- `POST /api/v1/analysis/predict` — Run AI disease prediction
- `POST /api/v1/eeg/record` — Record & analyze EEG data
- `GET /api/v1/research` — Search research papers
- `GET /api/v1/medications` — List medications
- `GET /api/v1/dashboard/stats` — Dashboard statistics
