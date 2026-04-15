from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from threading import Lock
from typing import Dict, Optional


class AuditLogger:
    """Append-only JSONL audit logger for decision and review events."""

    def __init__(self, path: Optional[str] = None, use_memory: Optional[bool] = None):
        self.path = path or os.path.join(os.getcwd(), "data", "audit_log.jsonl")
        self.use_memory = _resolve_memory_mode(use_memory)
        self._memory_records = []
        if not self.use_memory:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._lock = Lock()

    def log_event(self, event_type: str, payload: Dict):
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **payload,
        }
        with self._lock:
            if self.use_memory:
                self._memory_records.append(record)
                return
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _resolve_memory_mode(use_memory: Optional[bool]) -> bool:
    if use_memory is not None:
        return bool(use_memory)

    explicit = os.getenv("DEMO_MEMORY_FALLBACK")
    if explicit is not None:
        return explicit.strip().lower() in {"1", "true", "yes", "on"}

    return bool(os.getenv("VERCEL"))
