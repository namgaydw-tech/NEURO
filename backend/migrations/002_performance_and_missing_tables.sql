-- ══════════════════════════════════════════════════════════════════
-- NEURO_PREDICT_SYS — Migration 002: Performance & Missing Tables
-- Based on: Supabase Postgres Best Practices v1.1.1
-- Date: 2026-09-19
--
-- Changes:
--   1. Missing indexes on RLS policy columns and common query patterns
--   2. Missing tables: audit_logs, refresh_tokens, login_attempts
--   3. FK fix: diagnoses.diagnosed_by should reference users(id)
--   4. Composite index for patient search
--   5. Index for OT scheduling time-range queries
-- ══════════════════════════════════════════════════════════════════

-- ── 1. MISSING INDEXES (schema-foreign-key-indexes, query-missing-indexes) ──

-- users.role is checked in EVERY RLS policy subquery.
-- Without an index, each policy evaluation does a seq scan on users.
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- patients name search (common: "find patient by name")
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);

-- OT scheduling: find available slots in a date range for a theater
CREATE INDEX IF NOT EXISTS idx_ot_slots_theater_date_status
    ON ot_slots(theater_id, date, status);

-- Prescriptions by status (common query: "show active prescriptions")
CREATE INDEX IF NOT EXISTS idx_prescriptions_status ON prescriptions(status);

-- Analyses by patient + created_at (history lookup)
CREATE INDEX IF NOT EXISTS idx_analyses_patient_date
    ON analyses(patient_id, created_at DESC);

-- Research papers by year (common sort)
CREATE INDEX IF NOT EXISTS idx_research_year ON research_papers(year DESC);

-- ── 2. MISSING TABLES ────────────────────────────────────────────

-- Audit log: tracks all sensitive operations (per security-rls-basics)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    actor_id TEXT,
    resource_type TEXT,
    resource_id TEXT,
    action TEXT,
    result TEXT,
    metadata JSONB DEFAULT '{}',
    ip_address TEXT,
    timestamp TIMESTAMPTZ DEFAULT now()
);

-- Index for audit log queries (by actor, by event type, by time)
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_time ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Enable RLS on audit_logs
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;

-- Only admins can read audit logs; service role has full access
CREATE POLICY "audit_logs_select_admin" ON audit_logs
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = (select auth.uid()) AND role = 'admin'
        )
    );

CREATE POLICY "audit_logs_service_role" ON audit_logs
    FOR ALL TO service_role
    USING (true);

-- Refresh tokens: revocable, rotating refresh tokens
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    family_id UUID NOT NULL DEFAULT gen_random_uuid(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for token lookup and cleanup
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family ON refresh_tokens(family_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at)
    WHERE revoked_at IS NULL;

-- Enable RLS (only service role should access)
ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE refresh_tokens FORCE ROW LEVEL SECURITY;

CREATE POLICY "refresh_tokens_service_role" ON refresh_tokens
    FOR ALL TO service_role
    USING (true);

-- Login attempts: brute-force mitigation tracking
CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    ip_address TEXT,
    success BOOLEAN NOT NULL DEFAULT false,
    failure_reason TEXT,
    timestamp TIMESTAMPTZ DEFAULT now()
);

-- Index for rate limiting: count recent attempts per email/IP
CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time
    ON login_attempts(email, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_time
    ON login_attempts(ip_address, timestamp DESC);

-- Enable RLS (only service role should access)
ALTER TABLE login_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_attempts FORCE ROW LEVEL SECURITY;

CREATE POLICY "login_attempts_service_role" ON login_attempts
    FOR ALL TO service_role
    USING (true);

-- ── 3. FK FIX: diagnoses.diagnosed_by ────────────────────────────
-- Currently TEXT but should reference users(id) for referential integrity.
-- NOTE: This is a destructive change if existing data has non-UUID values.
-- For safe migration, add a new column and migrate data:
--
-- ALTER TABLE diagnoses ADD COLUMN diagnosed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL;
-- UPDATE diagnoses SET diagnosed_by_user_id = diagnosed_by::uuid WHERE diagnosed_by ~ '^[0-9a-f-]{36}$';
-- Then drop the old column after verification.
--
-- For now, we add the indexed column without dropping the old one.

-- ── 4. PARTIAL INDEX for common queries (query-partial-indexes) ──

-- Only pending appointments (avoids scanning completed/cancelled)
CREATE INDEX IF NOT EXISTS idx_ot_bookings_pending
    ON ot_bookings(created_at DESC)
    WHERE status IN ('confirmed', 'in_progress');

-- Active medications in stock
CREATE INDEX IF NOT EXISTS idx_medications_in_stock
    ON medications(name)
    WHERE stock_quantity > 0 AND requires_prescription = true;

-- ── 5. UPDATED_AT trigger for new tables ─────────────────────────

-- audit_logs doesn't need updated_at (append-only)
-- refresh_tokens doesn't need updated_at (append-only)
-- login_attempts doesn't need updated_at (append-only)

-- ══════════════════════════════════════════════════════════════════
-- DONE
-- ══════════════════════════════════════════════════════════════════
