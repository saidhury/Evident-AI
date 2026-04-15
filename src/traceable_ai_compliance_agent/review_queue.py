from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from threading import Lock
from typing import Dict, List, Optional


class ReviewQueue:
    """File-backed review queue for refused/low-confidence decisions."""

    def __init__(self, path: Optional[str] = None, use_memory: Optional[bool] = None):
        self.path = path or os.path.join(os.getcwd(), "data", "review_queue.json")
        self.use_memory = _resolve_memory_mode(use_memory)
        self._memory_entries: List[Dict] = []
        if not self.use_memory:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._lock = Lock()

    def _load(self) -> List[Dict]:
        if self.use_memory:
            return list(self._memory_entries)

        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, entries: List[Dict]):
        if self.use_memory:
            self._memory_entries = list(entries)
            return

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)

    def create_ticket(self, request: Dict, reason: str, trace_id: str) -> Dict:
        with self._lock:
            entries = self._load()
            ticket_id = f"TICKET-{len(entries) + 1}"
            entry = {
                "ticket_id": ticket_id,
                "status": "open",
                "reason": reason,
                "trace_id": trace_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "request": request,
                "actions": [],
            }
            entries.append(entry)
            self._save(entries)
            return entry

    def list_tickets(self, status: Optional[str] = None) -> List[Dict]:
        entries = self._load()
        if status:
            return [e for e in entries if e.get("status") == status]
        return entries

    def apply_action(self, ticket_id: str, action: str, reviewer: str, notes: str = "") -> Optional[Dict]:
        with self._lock:
            entries = self._load()
            for entry in entries:
                if entry.get("ticket_id") != ticket_id:
                    continue

                action_obj = {
                    "action": action,
                    "reviewer": reviewer or "unknown",
                    "notes": notes,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                entry.setdefault("actions", []).append(action_obj)

                if action in {"approve_override", "reject"}:
                    entry["status"] = "closed"

                self._save(entries)
                return entry

        return None

    def export_payload(self, status: Optional[str] = None) -> Dict:
        items = self.list_tickets(status=status)
        return {
            "count": len(items),
            "status_filter": status,
            "items": items,
        }


def _resolve_memory_mode(use_memory: Optional[bool]) -> bool:
    if use_memory is not None:
        return bool(use_memory)

    explicit = os.getenv("DEMO_MEMORY_FALLBACK")
    if explicit is not None:
        return explicit.strip().lower() in {"1", "true", "yes", "on"}

    return bool(os.getenv("VERCEL"))
