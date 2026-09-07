-- ══════════════════════════════════════════════════════════════════
-- NEURO_PREDICT_SYS — Supabase Database Schema
-- Run this in the Supabase SQL Editor to create all tables
-- ══════════════════════════════════════════════════════════════════

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Users Table ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'demo',
    department TEXT,
    clearance_level INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── Patients Table ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    gender TEXT,
    phone TEXT,
    email TEXT,
    medical_record_number TEXT UNIQUE,
    insurance_id TEXT,
    emergency_contact TEXT,
    allergies TEXT[] DEFAULT '{}',
    current_medications TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── Diagnoses Table ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS diagnoses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    disease_name TEXT NOT NULL,
    confidence_score REAL NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    severity TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'pending',
    symptoms TEXT[] DEFAULT '{}',
    notes TEXT,
    ai_prediction_id UUID,
    diagnosed_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── AI Analyses Table ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    predictions JSONB NOT NULL DEFAULT '[]',
    overall_risk TEXT DEFAULT 'low',
    ai_confidence REAL DEFAULT 0,
    brain_regions JSONB DEFAULT '{}',
    scan_progress REAL DEFAULT 0,
    run_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ── EEG Recordings Table ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS eeg_recordings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    channel_data JSONB NOT NULL,
    duration_seconds REAL NOT NULL,
    sample_rate INTEGER DEFAULT 256,
    signature_match JSONB,
    ai_insights TEXT[] DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ── Research Papers Table ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS research_papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    authors TEXT[] NOT NULL,
    abstract TEXT NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    journal TEXT,
    year INTEGER,
    doi TEXT UNIQUE,
    category TEXT,
    citations INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── Medications Table ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    generic_name TEXT,
    category TEXT NOT NULL,
    dosage_form TEXT NOT NULL,
    strength TEXT NOT NULL,
    manufacturer TEXT,
    stock_quantity INTEGER DEFAULT 0,
    requires_prescription BOOLEAN DEFAULT true,
    side_effects TEXT[] DEFAULT '{}',
    contraindications TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── Prescriptions Table ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prescriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    medication_id UUID REFERENCES medications(id),
    dosage TEXT NOT NULL,
    frequency TEXT NOT NULL,
    duration_days INTEGER NOT NULL,
    instructions TEXT,
    prescribed_by TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── OT Schedule Table ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ot_schedule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    surgery_type TEXT NOT NULL,
    surgeon_id UUID REFERENCES users(id),
    theater_number INTEGER NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    estimated_duration_minutes INTEGER DEFAULT 60,
    status TEXT DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── Indexes ──────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_patients_mrn ON patients(medical_record_number);
CREATE INDEX IF NOT EXISTS idx_diagnoses_patient ON diagnoses(patient_id);
CREATE INDEX IF NOT EXISTS idx_diagnoses_status ON diagnoses(status);
CREATE INDEX IF NOT EXISTS idx_analyses_patient ON analyses(patient_id);
CREATE INDEX IF NOT EXISTS idx_eeg_patient ON eeg_recordings(patient_id);
CREATE INDEX IF NOT EXISTS idx_research_category ON research_papers(category);
CREATE INDEX IF NOT EXISTS idx_medications_category ON medications(category);
CREATE INDEX IF NOT EXISTS idx_ot_schedule_time ON ot_schedule(scheduled_time);

-- ── Row Level Security (RLS) ─────────────────────────────────────
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnoses ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE eeg_recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ot_schedule ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read
CREATE POLICY "Allow authenticated read" ON patients FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated read" ON diagnoses FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated read" ON analyses FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated read" ON eeg_recordings FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated read" ON research_papers FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated read" ON medications FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated read" ON prescriptions FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated read" ON ot_schedule FOR SELECT USING (auth.role() = 'authenticated');

-- Allow service role full access (for backend API)
CREATE POLICY "Service role full access" ON users FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON patients FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON diagnoses FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON analyses FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON eeg_recordings FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON research_papers FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON medications FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON prescriptions FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON ot_schedule FOR ALL USING (auth.role() = 'service_role');
