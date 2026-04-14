from typing import Dict


class RefusalHandler:
    """Handles cases where the system must refuse and flag for human review."""

    def __init__(self):
        self._log = []

    def flag_for_review(self, request: Dict, reason: str) -> Dict:
        entry = {"request": request, "reason": reason}
        self._log.append(entry)
        # In prod, create a ticket, notify reviewers, persist to audit log
        return {"status": "flagged", "ticket_id": f"TICKET-{len(self._log)}", "reason": reason}

    def get_log(self):
        return list(self._log)
