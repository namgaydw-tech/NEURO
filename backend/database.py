"""
NEURO_PREDICT_SYS Database Layer
Provides in-memory demo storage and Supabase integration.
When SUPABASE_URL is not set, runs entirely in-memory for demo/dev.
"""
import uuid
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
try:
    from core.config import get_settings
except ImportError:
    from config import get_settings

settings = get_settings()


class InMemoryDB:
    """In-memory database for demo mode. Simulates table-based storage."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._tables: Dict[str, List[str]] = {}  # table_name -> [id, id, ...]

    def _get_table(self, table: str) -> Dict[str, Any]:
        if table not in self._store:
            self._store[table] = {}
        return self._store[table]

    def insert(self, table: str, data: dict, id_field: str = "id") -> dict:
        db = self._get_table(table)
        record_id = data.get(id_field) or str(uuid.uuid4())
        data[id_field] = record_id
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow().isoformat()
        db[record_id] = data.copy()
        if table not in self._tables:
            self._tables[table] = []
        if record_id not in self._tables[table]:
            self._tables[table].append(record_id)
        return data

    def get(self, table: str, record_id: str) -> Optional[dict]:
        db = self._get_table(table)
        return db.get(record_id)

    def get_all(self, table: str, filters: Optional[dict] = None) -> List[dict]:
        db = self._get_table(table)
        records = list(db.values())
        if filters:
            records = [
                r for r in records
                if all(r.get(k) == v for k, v in filters.items())
            ]
        return records

    def update(self, table: str, record_id: str, data: dict) -> Optional[dict]:
        db = self._get_table(table)
        if record_id in db:
            db[record_id].update(data)
            db[record_id]["updated_at"] = datetime.utcnow().isoformat()
            return db[record_id]
        return None

    def delete(self, table: str, record_id: str) -> bool:
        db = self._get_table(table)
        if record_id in db:
            del db[record_id]
            return True
        return False

    def count(self, table: str, filters: Optional[dict] = None) -> int:
        return len(self.get_all(table, filters))

    def search(self, table: str, field: str, query: str) -> List[dict]:
        db = self._get_table(table)
        query_lower = query.lower()
        return [
            r for r in db.values()
            if query_lower in str(r.get(field, "")).lower()
        ]


# Global instance
db = InMemoryDB()


class SupabaseDB:
    """Supabase-backed database. Used when SUPABASE_URL is configured."""

    def __init__(self):
        from supabase import create_client
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.admin_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
        )

    def insert(self, table: str, data: dict, id_field: str = "id") -> dict:
        if id_field not in data:
            data[id_field] = str(uuid.uuid4())
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow().isoformat()
        result = self.admin_client.table(table).insert(data).execute()
        return result.data[0] if result.data else data

    def get(self, table: str, record_id: str) -> Optional[dict]:
        result = self.client.table(table).select("*").eq("id", record_id).execute()
        return result.data[0] if result.data else None

    def get_all(self, table: str, filters: Optional[dict] = None) -> List[dict]:
        query = self.client.table(table).select("*")
        if filters:
            for k, v in filters.items():
                query = query.eq(k, v)
        result = query.execute()
        return result.data or []

    def update(self, table: str, record_id: str, data: dict) -> Optional[dict]:
        data["updated_at"] = datetime.utcnow().isoformat()
        result = self.admin_client.table(table).update(data).eq("id", record_id).execute()
        return result.data[0] if result.data else None

    def delete(self, table: str, record_id: str) -> bool:
        result = self.admin_client.table(table).delete().eq("id", record_id).execute()
        return True

    def count(self, table: str, filters: Optional[dict] = None) -> int:
        query = self.client.table(table).select("*", count="exact")
        if filters:
            for k, v in filters.items():
                query = query.eq(k, v)
        result = query.execute()
        return result.count or 0

    def search(self, table: str, field: str, query: str) -> List[dict]:
        result = self.client.table(table).select("*").ilike(field, f"%{query}%").execute()
        return result.data or []


def get_db():
    """Returns the appropriate database instance based on config."""
    if settings.DEMO_MODE:
        return db
    return SupabaseDB()
