from typing import List, Dict


class CitationValidator:
    """Validates that a decision is supported by retrieved citations.

    Simple policy: if retrieval returns >=1 strong match, accept; else refuse.
    Production: add entailment checks, citation scoring, and provenance URLs.
    """

    def validate(self, decision: Dict, evidence: List[Dict], min_evidence_score: float = 0.2) -> Dict:
        """Return {'ok': bool, 'evidence': List, 'reason': str}"""
        if not evidence:
            return {
                "ok": False,
                "evidence": [],
                "reason": "No supporting citations found",
                "evidence_quality": 0.0,
            }

        scores = [float(e.get("score", 0.0) or 0.0) for e in evidence]
        quality = sum(scores) / len(scores)
        if quality < min_evidence_score:
            return {
                "ok": False,
                "evidence": evidence,
                "reason": f"Evidence quality {quality:.2f} below threshold {min_evidence_score:.2f}",
                "evidence_quality": quality,
            }

        # Further logic could verify the evidence semantically supports the rationale
        return {
            "ok": True,
            "evidence": evidence,
            "reason": "Supported by citations",
            "evidence_quality": quality,
        }
