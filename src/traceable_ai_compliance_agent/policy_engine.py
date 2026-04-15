from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Dict, Optional


@dataclass
class PolicyResult:
    ok: bool
    reason: str
    rule_id: str


class PolicyEngine:
    """Simple configurable policy gate for production-like rule checks."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        policy_cfg = self.config.get("policy", {})
        self.version = policy_cfg.get("version", "2026-04-15")
        self.min_credit_score = policy_cfg.get("min_credit_score", 600)
        self.max_debt_to_income = policy_cfg.get("max_debt_to_income", 0.45)

    def evaluate(self, request: Dict) -> PolicyResult:
        applicant = request.get("applicant", {})
        credit_score = int(applicant.get("credit_score", 0) or 0)
        debt_to_income = applicant.get("debt_to_income")

        if credit_score < self.min_credit_score:
            return PolicyResult(
                ok=False,
                reason=f"Credit score {credit_score} below policy threshold {self.min_credit_score}",
                rule_id="CREDIT_SCORE_MIN",
            )

        if debt_to_income is not None:
            try:
                dti = float(debt_to_income)
                if dti > self.max_debt_to_income:
                    return PolicyResult(
                        ok=False,
                        reason=f"Debt-to-income {dti:.2f} exceeds policy threshold {self.max_debt_to_income:.2f}",
                        rule_id="DTI_MAX",
                    )
            except (TypeError, ValueError):
                return PolicyResult(
                    ok=False,
                    reason="Invalid debt_to_income format",
                    rule_id="DTI_FORMAT",
                )

        return PolicyResult(ok=True, reason="Policy checks passed", rule_id="PASS")

    def config_fingerprint(self) -> str:
        canonical = json.dumps(self.config, sort_keys=True, default=str)
        return sha256(canonical.encode("utf-8")).hexdigest()[:12]

    def counterfactual(self, request: Dict) -> Dict:
        applicant = request.get("applicant", {})
        credit_score = int(applicant.get("credit_score", 0) or 0)
        debt_to_income = applicant.get("debt_to_income")

        suggestions = []
        if credit_score < self.min_credit_score:
            suggestions.append(
                {
                    "field": "credit_score",
                    "current": credit_score,
                    "target_min": self.min_credit_score,
                    "delta_needed": self.min_credit_score - credit_score,
                    "why": "Meets minimum policy score threshold",
                }
            )

        if debt_to_income is not None:
            try:
                dti = float(debt_to_income)
                if dti > self.max_debt_to_income:
                    suggestions.append(
                        {
                            "field": "debt_to_income",
                            "current": dti,
                            "target_max": self.max_debt_to_income,
                            "delta_reduction_needed": round(dti - self.max_debt_to_income, 4),
                            "why": "Falls within DTI policy cap",
                        }
                    )
            except (TypeError, ValueError):
                suggestions.append(
                    {
                        "field": "debt_to_income",
                        "current": debt_to_income,
                        "target": "numeric <= policy max",
                        "why": "Invalid format prevents policy evaluation",
                    }
                )

        return {
            "available": bool(suggestions),
            "suggestions": suggestions,
        }
