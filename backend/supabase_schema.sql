-- ══════════════════════════════════════════════════════════════════
-- NEURO_PREDICT_SYS — Supabase Database Schema (v2)
-- Run in Supabase SQL Editor
-- ══════════════════════════════════════════════════════════════════

-- ── Extensions ───────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Helper: updated_at trigger ───────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ══════════════════════════════════════════════════════════════════
-- TABLES
-- ══════════════════════════════════════════════════════════════════

-- ── Users ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL CHECK (char_length(full_name) BETWEEN 1 AND 200),
    role TEXT NOT NULL DEFAULT 'demo'
        CHECK (role IN ('admin','neurologist','pharmacist','surgeon','researcher','demo')),
    department TEXT,
    clearance_level INTEGER DEFAULT 1 CHECK (clearance_level BETWEEN 1 AND 5),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── Patients ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name TEXT NOT NULL CHECK (char_length(first_name) BETWEEN 1 AND 100),
    last_name TEXT NOT NULL CHECK (char_length(last_name) BETWEEN 1 AND 100),
    date_of_birth DATE NOT NULL,
    gender TEXT CHECK (gender IN ('male','female','other','unspecified')),
    phone TEXT CHECK (char_length(phone) <= 30),
    email TEXT,
    medical_record_number TEXT UNIQUE,
    insurance_id TEXT,
    emergency_contact TEXT,
    allergies TEXT[] DEFAULT '{}',
    current_medications TEXT[] DEFAULT '{}',
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── Diagnoses ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS diagnoses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    disease_name TEXT NOT NULL CHECK (char_length(disease_name) BETWEEN 1 AND 200),
    confidence_score REAL NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    severity TEXT NOT NULL DEFAULT 'medium'
        CHECK (severity IN ('low','medium','high','critical')),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','in_progress','completed','reviewed')),
    symptoms TEXT[] DEFAULT '{}',
    notes TEXT,
    ai_prediction_id UUID,
    diagnosed_by TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_diagnoses_updated_at
    BEFORE UPDATE ON diagnoses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── AI Analyses ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    predictions JSONB NOT NULL DEFAULT '[]',
    overall_risk TEXT DEFAULT 'low'
        CHECK (overall_risk IN ('low','moderate','high','critical')),
    ai_confidence REAL DEFAULT 0 CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
    brain_regions JSONB DEFAULT '{}',
    scan_progress REAL DEFAULT 0 CHECK (scan_progress >= 0 AND scan_progress <= 100),
    run_by TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ── EEG Recordings ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS eeg_recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    channel_data JSONB NOT NULL,
    duration_seconds REAL NOT NULL CHECK (duration_seconds > 0),
    sample_rate INTEGER DEFAULT 256 CHECK (sample_rate > 0),
    signature_match JSONB,
    ai_insights TEXT[] DEFAULT '{}',
    notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ── Research Papers ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS research_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL CHECK (char_length(title) BETWEEN 1 AND 500),
    authors TEXT[] NOT NULL,
    abstract TEXT NOT NULL CHECK (char_length(abstract) <= 5000),
    keywords TEXT[] DEFAULT '{}',
    journal TEXT,
    year INTEGER CHECK (year BETWEEN 1900 AND 2100),
    doi TEXT UNIQUE,
    category TEXT CHECK (category IN (
        'alzheimers','parkinsons','ai_diagnostics','neurogenesis',
        'epilepsy','ms','brain_tumor','other'
    )),
    citations INTEGER DEFAULT 0 CHECK (citations >= 0),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_research_papers_updated_at
    BEFORE UPDATE ON research_papers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── Medications ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 200),
    generic_name TEXT,
    category TEXT NOT NULL CHECK (char_length(category) BETWEEN 1 AND 100),
    dosage_form TEXT NOT NULL CHECK (char_length(dosage_form) BETWEEN 1 AND 50),
    strength TEXT NOT NULL CHECK (char_length(strength) BETWEEN 1 AND 50),
    manufacturer TEXT,
    stock_quantity INTEGER DEFAULT 0 CHECK (stock_quantity >= 0),
    requires_prescription BOOLEAN DEFAULT true,
    side_effects TEXT[] DEFAULT '{}',
    contraindications TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_medications_updated_at
    BEFORE UPDATE ON medications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── Prescriptions ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prescriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    medication_id UUID REFERENCES medications(id) ON DELETE SET NULL,
    dosage TEXT NOT NULL CHECK (char_length(dosage) BETWEEN 1 AND 100),
    frequency TEXT NOT NULL CHECK (char_length(frequency) BETWEEN 1 AND 100),
    duration_days INTEGER NOT NULL CHECK (duration_days > 0),
    instructions TEXT,
    prescribed_by TEXT,
    status TEXT DEFAULT 'active'
        CHECK (status IN ('active','completed','cancelled')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_prescriptions_updated_at
    BEFORE UPDATE ON prescriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── OT Theaters ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ot_theaters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 100),
    location TEXT NOT NULL CHECK (char_length(location) BETWEEN 1 AND 200),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    equipment TEXT[] DEFAULT '{}',
    status TEXT DEFAULT 'available'
        CHECK (status IN ('available','maintenance','closed')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_ot_theaters_updated_at
    BEFORE UPDATE ON ot_theaters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── OT Time Slots ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ot_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    theater_id UUID NOT NULL REFERENCES ot_theaters(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL CHECK (end_time > start_time),
    slot_type TEXT DEFAULT 'available'
        CHECK (slot_type IN ('scheduled','available','blocked')),
    booked_by TEXT,
    patient_name TEXT,
    procedure TEXT,
    status TEXT DEFAULT 'available'
        CHECK (status IN ('available','booked','blocked','completed')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_ot_slots_updated_at
    BEFORE UPDATE ON ot_slots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── OT Bookings ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ot_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slot_id UUID NOT NULL REFERENCES ot_slots(id) ON DELETE CASCADE,
    patient_name TEXT NOT NULL CHECK (char_length(patient_name) BETWEEN 1 AND 200),
    patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    procedure TEXT NOT NULL CHECK (char_length(procedure) BETWEEN 1 AND 300),
    surgeon_name TEXT NOT NULL CHECK (char_length(surgeon_name) BETWEEN 1 AND 200),
    assistant_name TEXT,
    anesthesia_type TEXT DEFAULT 'general'
        CHECK (anesthesia_type IN ('general','local','regional','sedation')),
    priority TEXT DEFAULT 'normal'
        CHECK (priority IN ('normal','urgent','emergency')),
    status TEXT DEFAULT 'confirmed'
        CHECK (status IN ('confirmed','in_progress','completed','cancelled')),
    notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_ot_bookings_updated_at
    BEFORE UPDATE ON ot_bookings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── Pharmacy Profiles ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pharmacy_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pharmacy_name TEXT NOT NULL CHECK (char_length(pharmacy_name) BETWEEN 1 AND 200),
    pharmacy_code TEXT NOT NULL UNIQUE CHECK (char_length(pharmacy_code) BETWEEN 1 AND 50),
    license_number TEXT NOT NULL CHECK (char_length(license_number) BETWEEN 1 AND 100),
    address TEXT NOT NULL CHECK (char_length(address) BETWEEN 1 AND 500),
    phone TEXT NOT NULL CHECK (char_length(phone) BETWEEN 1 AND 30),
    email TEXT NOT NULL,
    operating_hours TEXT CHECK (char_length(operating_hours) <= 200),
    pharmacist_in_charge TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_pharmacy_profiles_updated_at
    BEFORE UPDATE ON pharmacy_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ══════════════════════════════════════════════════════════════════
-- INDEXES
-- ══════════════════════════════════════════════════════════════════

-- FK indexes (Postgres does NOT auto-index FK columns)
CREATE INDEX IF NOT EXISTS idx_patients_mrn ON patients(medical_record_number);
CREATE INDEX IF NOT EXISTS idx_patients_created_by ON patients(created_by);
CREATE INDEX IF NOT EXISTS idx_diagnoses_patient ON diagnoses(patient_id);
CREATE INDEX IF NOT EXISTS idx_diagnoses_status ON diagnoses(status);
CREATE INDEX IF NOT EXISTS idx_diagnoses_created_by ON diagnoses(created_by);
CREATE INDEX IF NOT EXISTS idx_analyses_patient ON analyses(patient_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_by ON analyses(created_by);
CREATE INDEX IF NOT EXISTS idx_eeg_patient ON eeg_recordings(patient_id);
CREATE INDEX IF NOT EXISTS idx_eeg_created_by ON eeg_recordings(created_by);
CREATE INDEX IF NOT EXISTS idx_research_category ON research_papers(category);
CREATE INDEX IF NOT EXISTS idx_medications_category ON medications(category);
CREATE INDEX IF NOT EXISTS idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_medication ON prescriptions(medication_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_created_by ON prescriptions(created_by);
CREATE INDEX IF NOT EXISTS idx_ot_slots_theater_date ON ot_slots(theater_id, date);
CREATE INDEX IF NOT EXISTS idx_ot_slots_status ON ot_slots(status);
CREATE INDEX IF NOT EXISTS idx_ot_bookings_slot ON ot_bookings(slot_id);
CREATE INDEX IF NOT EXISTS idx_ot_bookings_status ON ot_bookings(status);
CREATE INDEX IF NOT EXISTS idx_ot_bookings_created_by ON ot_bookings(created_by);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Partial index for active diagnoses (common query pattern)
CREATE INDEX IF NOT EXISTS idx_diagnoses_active ON diagnoses(created_at DESC)
    WHERE status IN ('pending', 'in_progress');

-- ══════════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY
-- ══════════════════════════════════════════════════════════════════

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnoses ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE eeg_recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ot_theaters ENABLE ROW LEVEL SECURITY;
ALTER TABLE ot_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE ot_bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE pharmacy_profiles ENABLE ROW LEVEL SECURITY;

-- Force RLS even for table owners (critical for Supabase)
ALTER TABLE users FORCE ROW LEVEL SECURITY;
ALTER TABLE patients FORCE ROW LEVEL SECURITY;
ALTER TABLE diagnoses FORCE ROW LEVEL SECURITY;
ALTER TABLE analyses FORCE ROW LEVEL SECURITY;
ALTER TABLE eeg_recordings FORCE ROW LEVEL SECURITY;
ALTER TABLE research_papers FORCE ROW LEVEL SECURITY;
ALTER TABLE medications FORCE ROW LEVEL SECURITY;
ALTER TABLE prescriptions FORCE ROW LEVEL SECURITY;
ALTER TABLE ot_theaters FORCE ROW LEVEL SECURITY;
ALTER TABLE ot_slots FORCE ROW LEVEL SECURITY;
ALTER TABLE ot_bookings FORCE ROW LEVEL SECURITY;
ALTER TABLE pharmacy_profiles FORCE ROW LEVEL SECURITY;

-- ── Helper: Check user role ──────────────────────────────────────
-- Use (select auth.uid()) pattern for RLS performance (called once, not per-row)

-- ══════════════════════════════════════════════════════════════════
-- RLS POLICIES
-- ══════════════════════════════════════════════════════════════════

-- ── USERS ────────────────────────────────────────────────────────
-- Users can read their own profile
CREATE POLICY "users_select_own" ON users
    FOR SELECT TO authenticated
    USING (id = (select auth.uid()));

-- Admins can read all users
CREATE POLICY "users_select_admin" ON users
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid()) AND role = 'admin'
        )
    );

-- Service role full access
CREATE POLICY "users_service_role" ON users
    FOR ALL TO service_role
    USING (true);

-- ── PATIENTS ─────────────────────────────────────────────────────
-- All authenticated users can read patients (medical staff need cross-department access)
CREATE POLICY "patients_select_auth" ON patients
    FOR SELECT TO authenticated
    USING (true);

-- Admins, neurologists, surgeons can create patients
CREATE POLICY "patients_insert_auth" ON patients
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','neurologist','surgeon')
        )
    );

-- Admins can update any patient; others can update patients they created
CREATE POLICY "patients_update_auth" ON patients
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid()) AND role = 'admin'
        )
        OR created_by = (select auth.uid())
    );

-- Only admins can delete patients
CREATE POLICY "patients_delete_admin" ON patients
    FOR DELETE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid()) AND role = 'admin'
        )
    );

-- Service role full access
CREATE POLICY "patients_service_role" ON patients
    FOR ALL TO service_role
    USING (true);

-- ── DIAGNOSES ────────────────────────────────────────────────────
-- All authenticated users can read diagnoses
CREATE POLICY "diagnoses_select_auth" ON diagnoses
    FOR SELECT TO authenticated
    USING (true);

-- Medical staff can create diagnoses
CREATE POLICY "diagnoses_insert_auth" ON diagnoses
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','neurologist','surgeon')
        )
    );

-- Admins can update any; others can update their own
CREATE POLICY "diagnoses_update_auth" ON diagnoses
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid()) AND role = 'admin'
        )
        OR created_by = (select auth.uid())
    );

-- Service role full access
CREATE POLICY "diagnoses_service_role" ON diagnoses
    FOR ALL TO service_role
    USING (true);

-- ── ANALYSES ─────────────────────────────────────────────────────
-- All authenticated users can read analyses
CREATE POLICY "analyses_select_auth" ON analyses
    FOR SELECT TO authenticated
    USING (true);

-- Medical staff can create analyses
CREATE POLICY "analyses_insert_auth" ON analyses
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','neurologist','researcher')
        )
    );

-- Service role full access
CREATE POLICY "analyses_service_role" ON analyses
    FOR ALL TO service_role
    USING (true);

-- ── EEG RECORDINGS ───────────────────────────────────────────────
-- All authenticated users can read EEG data
CREATE POLICY "eeg_select_auth" ON eeg_recordings
    FOR SELECT TO authenticated
    USING (true);

-- Medical staff can create EEG recordings
CREATE POLICY "eeg_insert_auth" ON eeg_recordings
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','neurologist')
        )
    );

-- Service role full access
CREATE POLICY "eeg_service_role" ON eeg_recordings
    FOR ALL TO service_role
    USING (true);

-- ── RESEARCH PAPERS (public read) ───────────────────────────────
-- Anyone (including anon) can read research papers
CREATE POLICY "research_select_public" ON research_papers
    FOR SELECT
    USING (true);

-- Authenticated users with researcher role can create
CREATE POLICY "research_insert_auth" ON research_papers
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','researcher')
        )
    );

-- Service role full access
CREATE POLICY "research_service_role" ON research_papers
    FOR ALL TO service_role
    USING (true);

-- ── MEDICATIONS (public read) ───────────────────────────────────
-- Anyone can read medications (drug catalog is public)
CREATE POLICY "medications_select_public" ON medications
    FOR SELECT
    USING (true);

-- Admins and pharmacists can create/update medications
CREATE POLICY "medications_insert_auth" ON medications
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','pharmacist')
        )
    );

CREATE POLICY "medications_update_auth" ON medications
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','pharmacist')
        )
    );

-- Service role full access
CREATE POLICY "medications_service_role" ON medications
    FOR ALL TO service_role
    USING (true);

-- ── PRESCRIPTIONS ────────────────────────────────────────────────
-- Medical staff can read prescriptions
CREATE POLICY "prescriptions_select_auth" ON prescriptions
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','neurologist','pharmacist','surgeon')
        )
    );

-- Medical staff can create prescriptions
CREATE POLICY "prescriptions_insert_auth" ON prescriptions
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','neurologist','surgeon')
        )
    );

-- Service role full access
CREATE POLICY "prescriptions_service_role" ON prescriptions
    FOR ALL TO service_role
    USING (true);

-- ── OT THEATERS ──────────────────────────────────────────────────
-- All authenticated users can read theaters
CREATE POLICY "theaters_select_auth" ON ot_theaters
    FOR SELECT TO authenticated
    USING (true);

-- Admins and surgeons can manage theaters
CREATE POLICY "theaters_insert_auth" ON ot_theaters
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','surgeon')
        )
    );

CREATE POLICY "theaters_update_auth" ON ot_theaters
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','surgeon')
        )
    );

-- Service role full access
CREATE POLICY "theaters_service_role" ON ot_theaters
    FOR ALL TO service_role
    USING (true);

-- ── OT SLOTS ─────────────────────────────────────────────────────
-- All authenticated users can read slots
CREATE POLICY "slots_select_auth" ON ot_slots
    FOR SELECT TO authenticated
    USING (true);

-- Medical staff can create/update slots
CREATE POLICY "slots_insert_auth" ON ot_slots
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','surgeon')
        )
    );

CREATE POLICY "slots_update_auth" ON ot_slots
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','surgeon')
        )
    );

-- Service role full access
CREATE POLICY "slots_service_role" ON ot_slots
    FOR ALL TO service_role
    USING (true);

-- ── OT BOOKINGS ──────────────────────────────────────────────────
-- All authenticated users can read bookings
CREATE POLICY "bookings_select_auth" ON ot_bookings
    FOR SELECT TO authenticated
    USING (true);

-- Medical staff can create bookings
CREATE POLICY "bookings_insert_auth" ON ot_bookings
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','surgeon')
        )
    );

-- Admins can update any; surgeons can update their own
CREATE POLICY "bookings_update_auth" ON ot_bookings
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid()) AND role = 'admin'
        )
        OR created_by = (select auth.uid())
    );

-- Service role full access
CREATE POLICY "bookings_service_role" ON ot_bookings
    FOR ALL TO service_role
    USING (true);

-- ── PHARMACY PROFILES ───────────────────────────────────────────
-- Pharmacists and admins can read pharmacy profiles
CREATE POLICY "pharmacy_select_auth" ON pharmacy_profiles
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','pharmacist')
        )
    );

-- Pharmacists and admins can create/update
CREATE POLICY "pharmacy_insert_auth" ON pharmacy_profiles
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','pharmacist')
        )
    );

CREATE POLICY "pharmacy_update_auth" ON pharmacy_profiles
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid())
            AND role IN ('admin','pharmacist')
        )
    );

-- Service role full access
CREATE POLICY "pharmacy_service_role" ON pharmacy_profiles
    FOR ALL TO service_role
    USING (true);
