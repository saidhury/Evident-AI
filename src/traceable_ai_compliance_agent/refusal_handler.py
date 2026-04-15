from typing import Dict


class RefusalHandler:
    """Handles cases where the system must refuse and flag for human review."""

    def __init__(self, review_queue=None):
        self._log = []
        self.review_queue = review_queue

    def flag_for_review(self, request: Dict, reason: str, trace_id: str = "") -> Dict:
        if self.review_queue is not None:
            ticket = self.review_queue.create_ticket(request=request, reason=reason, trace_id=trace_id)
            return {
                "status": "flagged",
                "ticket_id": ticket["ticket_id"],
                "reason": reason,
            }

        entry = {"request": request, "reason": reason}
        self._log.append(entry)
        # In prod, create a ticket, notify reviewers, persist to audit log
        return {"status": "flagged", "ticket_id": f"TICKET-{len(self._log)}", "reason": reason}

    def get_log(self):
        return list(self._log)
