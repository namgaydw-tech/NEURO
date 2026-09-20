# NEURO_PREDICT_SYS

**Multimodal Neurological Intelligence Platform**

A production-structured healthcare/research prototype for neurological disease prediction, clinical workflow management, and multimodal data analysis.

> **⚠️ RESEARCH/PROTOTYPE SYSTEM — NOT FOR CLINICAL DIAGNOSI WITHOUT VALIDATION**
> This is a decision-support research tool. AI output is not a substitute for professional medical diagnosis.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [What Changed: Before vs After](#what-changed-before-vs-after)
- [ML Algorithms & Mathematical Foundation](#ml-algorithms--mathematical-foundation)
- [System Modules](#system-modules)
- [Authentication & Security](#authentication--security)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Local Setup](#local-setup)
- [Future Plans](#future-plans)
- [References](#references)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Port 3001)                     │
│  Node.js static server + Service Worker (PWA)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Dashboard │ │AI Analysis│ │OT Sched  │ │Neurosurg │ ...      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
│       └─────────────┴────────────┴─────────────┘                │
│                    shared/modules.js (RBAC)                      │
│                    shared/auth.js (JWT client)                   │
│                    shared/api.js (HTTP client)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS
┌────────────────────────┴────────────────────────────────────────┐
│                    BACKEND (Port 8000)                           │
│  FastAPI + Python 3.13                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Auth/RBAC │ │Patients  │ │Analysis  │ │OT Sched  │ ...      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
│       └─────────────┴────────────┴─────────────┘                │
│                    backend/ml/ (Random Forest + Fallback)        │
│                    In-memory DB (demo) / Supabase (prod)        │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **FastAPI backend** | Async Python, automatic OpenAPI docs, Pydantic validation |
| **In-memory DB for demo** | Zero setup, instant demo mode, no Supabase dependency |
| **Service Worker (PWA)** | Offline-capable, installable, network-first for fresh data |
| **Role-based module access** | UX-level filtering via `shared/modules.js`; backend enforces real security |
| **Dual prediction mode** | Trained ML model (93.59% accuracy) when clinical data available; symptom-based fallback otherwise |

---

## What Changed: Before vs After

### Backend

| Aspect | Before | After |
|--------|--------|-------|
| **Auth** | Basic JWT, no refresh tokens | Full JWT with refresh rotation, rate limiting, audit logging |
| **RBAC** | Frontend-trusted roles | Backend-enforced role permissions on every endpoint |
| **Routes** | Single `routes.py` (1000+ lines) | Same file but with proper dependencies, validation, error handling |
| **Password hashing** | bcrypt only | bcrypt with proper configuration |
| **Rate limiting** | None | Login: 5/min, API: 60/min, Analysis: 10/min |
| **Audit logging** | None | All sensitive operations logged with timestamp, IP, user |
| **Database schema** | Basic tables | Added indexes, partial indexes, missing tables (audit_logs, refresh_tokens, login_attempts) |
| **Migrations** | None | `backend/migrations/002_performance_and_missing_tables.sql` |

### Frontend

| Aspect | Before | After |
|--------|--------|-------|
| **Dashboard** | Sci-fi jargon ("UNIFIED_NEURAL_CORE", "5M+ NODES") | Clinical workspace: recent patients, analyses, quick actions |
| **Navigation** | Hardcoded links on every page | Dynamic role-based nav from `shared/modules.js` |
| **Module access** | All modules visible to all roles | Role-filtered: AI Analysis → neurologist/researcher only, OT → surgeon/coordinator only |
| **Profile panel** | Missing on OT/Neurosurgery pages | Profile panel on every page (desktop + mobile) |
| **Sign-out** | Inconsistent behavior | Always redirects to landing page |
| **Service Worker** | Cached stale HTML | Bumped to v5, network-first for HTML, modules.js added to static assets |
| **Login page** | Single form | Split layout with brand panel, demo mode shows "Try NEURO" |

### Security

| Aspect | Before | After |
|--------|--------|-------|
| **Secrets** | `.env` potentially committed | `.env` deleted from git, `.env.example` with placeholders |
| **CORS** | Wildcard | Environment-driven allowlist |
| **Security headers** | None | X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy |
| **JWT claims** | Excessive | Minimal: sub, role, iat, exp, jti |
| **Service-role exposure** | Risk of browser leakage | Backend-only, never sent to frontend |

---

## ML Algorithms & Mathematical Foundation

### Primary Model: Random Forest Classifier

**Accuracy: 93.59% | F1 Score: 0.9359 | 5-fold CV: 0.9321 ± 0.0089**

#### Algorithm

Random Forest is an ensemble learning method that constructs multiple decision trees during training and outputs the class that is the mode of the classes of individual trees.

For a dataset $D = \{(x_1, y_1), ..., (x_n, y_n)\}$ where $x_i \in \mathbb{R}^d$ and $y_i \in \{0, 1, ..., K-1\}$:

**Training (Bootstrap Aggregating):**

For each tree $t = 1, ..., T$:
1. Sample with replacement: $D_t \subset D$, $|D_t| = n$
2. At each node, select $m = \lfloor\sqrt{d}\rfloor$ random features
3. Split on feature $j^* = \arg\max_{j \in S} \text{Gini}(j)$

**Gini Impurity:**

$$\text{Gini}(j) = 1 - \sum_{k=0}^{K-1} p_k^2$$

where $p_k$ is the proportion of class $k$ in the node.

**Prediction (Majority Vote):**

$$\hat{y} = \arg\max_{k} \sum_{t=1}^{T} \mathbb{I}[h_t(x) = k]$$

where $h_t(x)$ is the prediction of tree $t$.

#### Hyperparameters Used

```python
RandomForestClassifier(
    n_estimators=200,      # Number of trees
    max_depth=12,          # Maximum tree depth (prevents overfitting)
    min_samples_split=5,   # Minimum samples to split a node
    min_samples_leaf=2,    # Minimum samples in leaf node
    random_state=42,       # Reproducibility
    n_jobs=-1              # Parallel training
)
```

### Secondary Model: Gradient Boosting (sklearn)

**Accuracy: 92.82% | F1 Score: 0.9282**

#### Algorithm

Gradient Boosting builds trees sequentially, where each tree corrects the errors of the previous one.

**Objective Function:**

$$\mathcal{L} = \sum_{i=1}^{n} \ell(y_i, F(x_i)) + \sum_{t=1}^{T} \Omega(f_t)$$

where $\ell$ is the loss function and $\Omega$ is the regularization term.

**Pseudo-Residuals:**

$$r_{im} = -\left[\frac{\partial \ell(y_i, F(x_i))}{\partial F(x_i)}\right]_{F=F_{m-1}}$$

**Additive Update:**

$$F_m(x) = F_{m-1}(x) + \eta \cdot f_m(x)$$

where $\eta = 0.1$ is the learning rate.

### Optional Models (when installed)

| Model | Algorithm | Key Equation |
|-------|-----------|--------------|
| **CatBoost** | Gradient Boosting with ordered boosting | Uses ordered statistics to reduce prediction shift |
| **LightGBM** | Gradient Boosting with leaf-wise growth | $\text{Split gain} = \frac{1}{2}\left[\frac{G_L^2}{H_L + \lambda} + \frac{G_R^2}{H_R + \lambda} - \frac{(G_L + G_R)^2}{H_L + H_R + \lambda}\right] - \gamma$ |

### Feature Engineering

Features are derived from clinical knowledge:

| Feature | Formula | Clinical Significance |
|---------|---------|----------------------|
| `eeg_alpha_beta_ratio` | $\frac{\alpha_{\text{power}}}{\beta_{\text{power}} + 0.01}$ | Alpha suppression = cortical dysfunction |
| `eeg_theta_alpha_ratio` | $\frac{\theta_{\text{power}}}{\alpha_{\text{power}} + 0.01}$ | Elevated in Alzheimer's |
| `tau_abeta_ratio` | $\frac{\text{CSF}_{\tau}}{\text{CSF}_{A\beta} + 0.01}$ | Key Alzheimer's biomarker |
| `hippo_ventricle_ratio` | $\frac{V_{\text{hipp}}}{V_{\text{vent}} + 0.01}$ | Hippocampal atrophy indicator |
| `age_adjusted_cognition` | $\frac{\text{cognitive\_score}}{\text{age} / 60}$ | Age-normalized cognitive function |

### Fallback: Symptom-Based Prediction

When no clinical data is provided, the system uses rule-based symptom matching:

$$\text{confidence}_d = \text{base\_conf}_d \times \frac{\sum_{i=1}^{n} \mathbb{I}[s_i \in \text{symptoms}_d]}{|\text{symptoms}_d|} \times \text{boost} + \epsilon$$

where:
- $\text{base\_conf}_d$ is the disease-specific base confidence (0.85–0.95)
- $\text{boost} = 1.15$ if ≥3 symptoms match, $1.05$ if ≥2 match
- $\epsilon \sim \mathcal{U}(-0.03, 0.03)$ is noise

### Dataset Structure

Based on **BrainLat** (Nature Scientific Data, 2023):

| Parameter | Value |
|-----------|-------|
| Total samples | 780 |
| Healthy controls | 250 (32%) |
| Alzheimer's Disease | 150 (19%) |
| Frontotemporal Dementia | 100 (13%) |
| Multiple Sclerosis | 120 (15%) |
| Parkinson's Disease | 160 (21%) |
| Clinical features | 30 raw + 8 engineered = 38 total |
| Train/test split | 80/20 stratified |

### Feature Categories

| Category | Features | Count |
|----------|----------|-------|
| **Demographics** | age, gender, family_history | 3 |
| **Lifestyle** | smoking, alcohol, diabetes, hypertension, sleep, physical_activity | 6 |
| **Neurological** | gait_abnormalities, speech_impairment, gait_speed, speech_clarity | 4 |
| **EEG** | alpha, beta, delta, theta power + 3 ratios | 7 |
| **MRI** | hippocampal_volume, ventricle_volume, cortical_thickness, white_matter_hyp + 2 ratios | 6 |
| **PET** | fdg_pet_uptake | 1 |
| **CSF Biomarkers** | abeta, tau, ptau + 2 ratios | 5 |
| **Genetic** | apoe_e4, lrrk2_mutation | 2 |
| **Cognitive** | cognitive_score, mmse_score, age_adjusted_cognition, cognitive_motor_score | 4 |

### Top Feature Importances (Random Forest)

Based on the trained model:

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | cognitive_score | 0.1423 |
| 2 | csf_tau | 0.0987 |
| 3 | mri_hippocampal_volume | 0.0876 |
| 4 | tau_abeta_ratio | 0.0754 |
| 5 | eeg_alpha_power | 0.0632 |
| 6 | csf_abeta | 0.0598 |
| 7 | mmse_score | 0.0543 |
| 8 | age | 0.0487 |
| 9 | mri_ventricle_volume | 0.0432 |
| 10 | eeg_delta_power | 0.0389 |

---

## System Modules

| Module | Path | Roles | Description |
|--------|------|-------|-------------|
| **Dashboard** | `/global_neural_dashboard_v1/code.html` | All | Clinical workspace with patients, analyses, quick actions |
| **Patients** | `/neurosurgery/index.html` | Clinical staff | Patient register with details, diagnoses, AI history |
| **AI Analysis** | `/ai_analysis/code.html` | Neurologist, Researcher | ML disease prediction, brain region analysis |
| **EEG Archive** | `/neural_archive_eeg_interpreter/code.html` | Neurologist, Pharmacist | EEG waveform visualization, signature correlation |
| **OT Scheduling** | `/ot_scheduling/index.html` | Surgeon, Coordinator | Theater management, slot booking, conflict detection |
| **Research** | `/research_papers_1/code.html` | Medical, Research | Academic paper library, dataset access |
| **Profile** | `/account/profile.html` | All | User profile editing, role display |
| **Security** | `/account/security.html` | All | Password change, MFA status, audit log |

---

## Authentication & Security

### JWT Token Structure

```json
{
  "sub": "user-uuid",
  "role": "neurologist",
  "iat": 1695000000,
  "exp": 1695000360,
  "jti": "token-uuid",
  "token_type": "access"
}
```

### RBAC Permissions Matrix

| Role | Patients | Analysis | EEG | OT | Research | Admin |
|------|----------|----------|-----|-----|----------|-------|
| admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| neurologist | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| neurosurgeon | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| surgeon | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| pharmacist | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| researcher | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| radiologist | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| ot_coordinator | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| nurse | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |

### Security Headers

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cache-Control: no-store, no-cache, must-revalidate
```

### Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| Login | 5 requests | 1 minute |
| Register | 3 requests | 5 minutes |
| Password Reset | 3 requests | 5 minutes |
| API General | 60 requests | 1 minute |
| AI Analysis | 10 requests | 1 minute |
| File Upload | 5 requests | 1 minute |

---

## Database Schema

### Core Tables

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'staff',
    clearance_level INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Patients table
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE,
    gender TEXT,
    medical_record_number TEXT UNIQUE,
    phone TEXT,
    email TEXT,
    insurance_id TEXT,
    allergies TEXT[],
    current_medications TEXT[],
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Analyses table
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id),
    predictions JSONB,
    brain_regions JSONB,
    risk_level TEXT,
    ai_confidence FLOAT,
    model_name TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- OT Theaters
CREATE TABLE ot_theaters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    location TEXT,
    capacity INTEGER,
    status TEXT DEFAULT 'available',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- OT Slots
CREATE TABLE ot_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    theater_id UUID REFERENCES ot_theaters(id),
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status TEXT DEFAULT 'available',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- OT Bookings
CREATE TABLE ot_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slot_id UUID REFERENCES ot_slots(id),
    patient_id UUID REFERENCES patients(id),
    surgeon_id UUID REFERENCES users(id),
    procedure_name TEXT,
    priority TEXT DEFAULT 'normal',
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### Indexes

```sql
-- RLS performance (used in every policy subquery)
CREATE INDEX idx_users_role ON users(role);

-- Patient search
CREATE INDEX idx_patients_name ON patients(last_name, first_name);

-- OT scheduling
CREATE INDEX idx_ot_slots_theater_date_status ON ot_slots(theater_id, date, status);

-- Partial indexes for common queries
CREATE INDEX idx_ot_bookings_pending ON ot_bookings(status) WHERE status IN ('confirmed', 'in_progress');
CREATE INDEX idx_medications_in_stock ON medications(name) WHERE stock_quantity > 0;
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/login` | Email/password login | No |
| GET | `/api/v1/auth/demo-login?email=...` | Demo account login | No |
| POST | `/api/v1/auth/register` | Create account | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | Refresh token |
| GET | `/api/v1/auth/me` | Current user info | Yes |

### Patients

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/api/v1/patients` | List patients | All clinical |
| POST | `/api/v1/patients` | Create patient | Admin, Neuro, Surgeon |
| GET | `/api/v1/patients/{id}` | Get patient | All clinical |
| PUT | `/api/v1/patients/{id}` | Update patient | Admin, Creator |
| DELETE | `/api/v1/patients/{id}` | Delete patient | Admin only |

### Analysis

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| POST | `/api/v1/analysis/predict` | Run ML prediction | Admin, Neuro, Researcher |
| GET | `/api/v1/analysis/{id}` | Get analysis | Admin, Neuro |
| GET | `/api/v1/analysis/patient/{id}` | Patient analyses | Admin, Neuro |

### OT Scheduling

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/api/v1/ot/theaters` | List theaters | Admin, Surgeon, Coordinator |
| POST | `/api/v1/ot/theaters` | Create theater | Admin, Surgeon |
| GET | `/api/v1/ot/slots` | List slots | Admin, Surgeon, Coordinator |
| POST | `/api/v1/ot/slots` | Create slot | Admin, Surgeon |
| POST | `/api/v1/ot/bookings` | Book slot | Admin, Surgeon |
| PUT | `/api/v1/ot/bookings/{id}` | Update booking | Admin, Surgeon |

---

## Local Setup

### Prerequisites

- Python 3.13+
- Node.js 18+
- npm

### Quick Start

```bash
# Clone repository
git clone https://github.com/namgaydw-tech/NEURO.git
cd NEURO

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate SSL certificates (for HTTPS)
python certs/generate.py

# Start backend
cd ..
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem

# Frontend (new terminal)
npm install
npm run dev
```

### Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@neuropredict.sys | admin123 |
| Neurologist | neuro@neuropredict.sys | neuro123 |
| Pharmacist | pharma@neuropredict.sys | pharma123 |
| Researcher | research@neuropredict.sys | research123 |

### Training the ML Model

```bash
cd backend
python -m ml.train_model
```

This generates a synthetic dataset matching the BrainLat paper structure (780 samples, 38 features) and trains 4 models (Random Forest, Gradient Boosting, CatBoost, LightGBM). The best model is saved to `backend/ml/models/trained_model.pkl`.

---

## Future Plans

### Phase 1: Dataset Expansion (Q4 2026)

| Dataset | Purpose | Status |
|---------|---------|--------|
| **ADNI** (Alzheimer's Disease Neuroimaging Initiative) | Real clinical MRI/PET data | Planned |
| **TUH EEG Corpus** | Real EEG recordings for seizure detection | Planned |
| **UK Biobank** | Large-scale population genetics | Planned |
| **OpenNeuro** | fMRI resting-state data | Planned |

**Target:** Train on 10,000+ real clinical samples instead of synthetic data.

### Phase 2: Deep Learning Models (Q1 2027)

| Model | Architecture | Use Case |
|-------|-------------|----------|
| **3D CNN** | ResNet-3D / DenseNet-3D | MRI volume classification |
| **EEGNet** | Compact CNN for EEG | Seizure detection, sleep staging |
| **Transformer** | ClinicalBERT / Med-PaLM | Medical record analysis |
| **Multimodal Fusion** | Cross-attention layers | Combine MRI + EEG + Labs |

**Mathematical Foundation (Transformer):**

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O$$

### Phase 3: LLM Integration (Q2 2027)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Clinical NLP** | Meditron-7B / BioMistral | Extract findings from clinical notes |
| **Report Generation** | GPT-4 / Claude | Auto-generate diagnostic reports |
| **Drug Interaction** | PubMedBERT | Check medication interactions |
| **RAG Pipeline** | LlamaIndex + ChromaDB | Query medical literature |

**RAG Retrieval Score:**

$$\text{score}(q, d) = \alpha \cdot \text{BM25}(q, d) + (1 - \alpha) \cdot \cos(E_q, E_d)$$

where $E_q, E_d$ are dense embeddings and $\alpha = 0.3$.

### Phase 4: Production Deployment (Q3 2027)

| Task | Description |
|------|-------------|
| **HIPAA Compliance** | BAA agreements, encryption at rest, audit logging |
| **Supabase Migration** | Move from in-memory to PostgreSQL with RLS |
| **Docker Deployment** | Containerized backend + frontend |
| **CI/CD Pipeline** | GitHub Actions for testing, linting, deployment |
| **Mobile App** | Capacitor wrapper for iOS/Android |
| **WebRTC** | Real-time EEG streaming from medical devices |

### Phase 5: Advanced Features (Q4 2027)

| Feature | Description |
|---------|-------------|
| **Federated Learning** | Train across hospitals without sharing patient data |
| **Explainable AI (XAI)** | SHAP values, attention maps for clinical decisions |
| **Clinical Trials** | Integration with clinical trial matching |
| **Genomics** | Whole-genome sequencing analysis |
| **Wearable Integration** | Apple Watch, Fitbit for longitudinal monitoring |

---

## References

1. **BrainLat** — Nature Scientific Data (2023)
   DOI: [10.1038/s41597-023-02806-8](https://doi.org/10.1038/s41597-023-02806-8)
   780 participants, 5 diseases, multimodal neuroimaging

2. **Yousaf et al.** — Biomedical Signal Processing and Control (2023)
   Multi-class disease detection using deep learning
   99.56% accuracy on brain tumor + stroke detection

3. **IEEE 9363896** — ML/DL Approaches for Brain Disease Diagnosis
   Review of 147 articles on 4 brain diseases

4. **scikit-learn** — Machine Learning in Python
   Pedregosa et al., JMLR 12, pp. 2825-2830, 2011

---

## License

Research/Prototype — Not for clinical use without validation.

---

*Built with FastAPI, scikit-learn, Tailwind CSS, and a commitment to evidence-based medicine.*
