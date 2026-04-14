from typing import List, Dict


class CitationValidator:
    """Validates that a decision is supported by retrieved citations.

    Simple policy: if retrieval returns >=1 strong match, accept; else refuse.
    Production: add entailment checks, citation scoring, and provenance URLs.
    """

    def validate(self, decision: Dict, evidence: List[Dict]) -> Dict:
        """Return {'ok': bool, 'evidence': List, 'reason': str}"""
        if not evidence:
            return {"ok": False, "evidence": [], "reason": "No supporting citations found"}
        # Further logic could verify the evidence semantically supports the rationale
        return {"ok": True, "evidence": evidence, "reason": "Supported by citations"}
