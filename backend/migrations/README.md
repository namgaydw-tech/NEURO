# NEURO_PREDICT_SYS — Database Migrations

## Migration History

| Migration | Date | Description |
|-----------|------|-------------|
| 001 | 2026-09-07 | Initial schema: users, patients, diagnoses, analyses, eeg, research, medications, prescriptions, OT, pharmacy |
| 002 | 2026-09-19 | Performance indexes, missing tables (audit_logs, refresh_tokens, login_attempts), FK fixes |

## Applying Migrations

### Fresh database
```bash
# Run in Supabase SQL Editor or psql:
cat backend/supabase_schema.sql | psql $DATABASE_URL
cat backend/migrations/002_performance_and_missing_tables.sql | psql $DATABASE_URL
```

### Existing database
```bash
# Run only the new migration:
cat backend/migrations/002_performance_and_missing_tables.sql | psql $DATABASE_URL
```

## Best Practices Applied (Supabase Postgres v1.1.1)

### schema-primary-keys
- Current: `UUID DEFAULT gen_random_uuid()` (UUIDv4)
- Note: For new tables in distributed systems, prefer UUIDv7 (time-ordered) to avoid index fragmentation
- Existing tables: UUIDv4 kept for compatibility; new tables should consider UUIDv7

### schema-data-types
- ✅ Uses `TEXT` not `VARCHAR(n)` (same performance, no artificial limits)
- ✅ Uses `TIMESTAMPTZ` not `TIMESTAMP`
- ✅ Uses `BOOLEAN` not varchar/integer
- ✅ Uses `JSONB` for structured data
- ✅ Uses `TEXT[]` for arrays

### schema-constraints
- ✅ `CHECK` constraints on all enum-like columns
- ✅ `UNIQUE` constraints where needed
- ✅ `NOT NULL` on required fields
- ✅ `REFERENCES` for foreign keys with `ON DELETE` behavior
- All constraints use `IF NOT EXISTS` pattern via `DO $$ ... END $$` blocks where needed

### schema-foreign-key-indexes
- ✅ All FK columns indexed (patients.created_by, diagnoses.patient_id, etc.)
- ✅ Added: `idx_users_role` for RLS policy subqueries
- ✅ Added: `idx_ot_slots_theater_date_status` for scheduling queries

### query-missing-indexes
- ✅ Added: `idx_patients_name` for patient search
- ✅ Added: `idx_prescriptions_status` for status filtering
- ✅ Added: `idx_analyses_patient_date` for history lookup
- ✅ Added: `idx_research_year` for sort queries
- ✅ Partial index: `idx_diagnoses_active` for pending/in-progress only
- ✅ Partial index: `idx_ot_bookings_pending` for confirmed/in-progress only
- ✅ Partial index: `idx_medications_in_stock` for in-stock medications

### query-partial-indexes
- ✅ Partial indexes for common filtered queries (active diagnoses, pending bookings, in-stock medications)

### security-rls-basics
- ✅ RLS enabled on ALL tables
- ✅ RLS forced on ALL tables (prevents table-owner bypass)
- ✅ Policies use `(select auth.uid())` pattern (evaluated once, not per-row)
- ✅ Role-based access: admin, neurologist, surgeon, pharmacist, researcher
- ✅ Service role full access for backend operations
- ✅ Public read for research_papers and medications (drug catalog)

### security-rls-performance
- ✅ RLS policies use subquery pattern `(select auth.uid())` not `auth.uid()` directly
- ✅ Added index on `users.role` to speed up policy subqueries
- ✅ Composite indexes for multi-column policy checks

### data-pagination
- Consider cursor-based pagination for large result sets (audit_logs, patients)

### lock-short-transactions
- Backend uses short transactions for OT slot booking (check + insert)
- Inventory operations use atomic decrement

## Missing (Future Work)

1. **UUIDv7**: Consider `pg_uuidv7` extension for new tables
2. **Partitioning**: `audit_logs` and `login_attempts` should be partitioned by time when data grows
3. **Connection pooling**: Use PgBouncer or Supabase connection pooler for production
4. **Vacuum tuning**: Monitor `autovacuum` settings for large tables
