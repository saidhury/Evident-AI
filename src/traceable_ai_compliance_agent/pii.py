from __future__ import annotations

from typing import Any


SENSITIVE_KEYS = {
    "name",
    "first_name",
    "last_name",
    "email",
    "phone",
    "mobile",
    "ssn",
    "pan",
    "aadhaar",
    "address",
    "dob",
    "birth_date",
}


def _mask_value(value: Any) -> Any:
    if value is None:
        return None
    text = str(value)
    if len(text) <= 2:
        return "**"
    return f"{text[:1]}{'*' * max(2, len(text) - 2)}{text[-1:]}"


def mask_pii(payload: Any) -> Any:
    """Recursively masks commonly sensitive fields in dictionaries/lists."""
    if isinstance(payload, dict):
        out = {}
        for key, value in payload.items():
            if key.lower() in SENSITIVE_KEYS:
                out[key] = _mask_value(value)
            else:
                out[key] = mask_pii(value)
        return out
    if isinstance(payload, list):
        return [mask_pii(item) for item in payload]
    return payload
