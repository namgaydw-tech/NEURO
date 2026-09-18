"""
NEURO_PREDICT_SYS — Database Layer
Supabase client with in-memory fallback for demo mode.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from .config import get_settings

settings = get_settings()


# ── In-Memory DB (demo mode) ──────────────────────────────────────

class InMemoryDB:
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def _table(self, name: str) -> Dict[str, Any]:
        if name not in self._store:
            self._store[name] = {}
        return self._store[name]

    def insert(self, table: str, data: dict, id_field: str = "id") -> dict:
        t = self._table(table)
        rid = data.get(id_field) or str(uuid.uuid4())
        data[id_field] = rid
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow().isoformat()
        t[rid] = data.copy()
        return data

    def get(self, table: str, record_id: str) -> Optional[dict]:
        return self._table(table).get(record_id)

    def get_all(self, table: str, filters: Optional[dict] = None) -> List[dict]:
        records = list(self._table(table).values())
        if filters:
            records = [r for r in records if all(r.get(k) == v for k, v in filters.items())]
        return records

    def update(self, table: str, record_id: str, data: dict) -> Optional[dict]:
        t = self._table(table)
        if record_id in t:
            t[record_id].update(data)
            t[record_id]["updated_at"] = datetime.utcnow().isoformat()
            return t[record_id]
        return None

    def delete(self, table: str, record_id: str) -> bool:
        t = self._table(table)
        if record_id in t:
            del t[record_id]
            return True
        return False

    def count(self, table: str, filters: Optional[dict] = None) -> int:
        return len(self.get_all(table, filters))

    def search(self, table: str, field: str, query: str) -> List[dict]:
        q = query.lower()
        return [r for r in self._table(table).values() if q in str(r.get(field, "")).lower()]

    def query(self, table: str, sql: str, params: tuple = ()) -> List[dict]:
        """SQL passthrough — no-op for in-memory, real SQL for Supabase."""
        return []


# ── Supabase Client ───────────────────────────────────────────────

class SupabaseDB:
    def __init__(self):
        from supabase import create_client
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        self.admin = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_ANON_KEY,
        )

    def insert(self, table: str, data: dict, id_field: str = "id") -> dict:
        if id_field not in data:
            data[id_field] = str(uuid.uuid4())
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow().isoformat()
        result = self.admin.table(table).insert(data).execute()
        return result.data[0] if result.data else data

    def get(self, table: str, record_id: str) -> Optional[dict]:
        result = self.client.table(table).select("*").eq("id", record_id).execute()
        return result.data[0] if result.data else None

    def get_all(self, table: str, filters: Optional[dict] = None) -> List[dict]:
        q = self.client.table(table).select("*")
        if filters:
            for k, v in filters.items():
                q = q.eq(k, v)
        return q.execute().data or []

    def update(self, table: str, record_id: str, data: dict) -> Optional[dict]:
        data["updated_at"] = datetime.utcnow().isoformat()
        result = self.admin.table(table).update(data).eq("id", record_id).execute()
        return result.data[0] if result.data else None

    def delete(self, table: str, record_id: str) -> bool:
        self.admin.table(table).delete().eq("id", record_id).execute()
        return True

    def count(self, table: str, filters: Optional[dict] = None) -> int:
        q = self.client.table(table).select("*", count="exact")
        if filters:
            for k, v in filters.items():
                q = q.eq(k, v)
        result = q.execute()
        return result.count or 0

    def search(self, table: str, field: str, query: str) -> List[dict]:
        result = self.client.table(table).select("*").ilike(field, f"%{query}%").execute()
        return result.data or []

    def query(self, table: str, sql: str, params: tuple = ()) -> List[dict]:
        """Raw SQL query via Supabase RPC or direct."""
        try:
            result = self.admin.rpc("run_query", {"query_text": sql}).execute()
            return result.data or []
        except Exception:
            return []


# ── Singleton ─────────────────────────────────────────────────────

_db = None


def get_db():
    global _db
    if _db is None:
        if settings.DEMO_MODE:
            _db = InMemoryDB()
            print("[DB] Using in-memory database (demo mode)")
        else:
            _db = SupabaseDB()
            print(f"[DB] Connected to Supabase: {settings.SUPABASE_URL[:40]}...")
    return _db
