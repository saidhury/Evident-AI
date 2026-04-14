from typing import Dict


class DecisionEngine:
    """Generates preliminary decisions using an LLM.

    This is a minimal stub. Integrate with LangChain or direct LLM calls
    in production.
    """

    def __init__(self, model: str = "gpt-4"):
        self.model = model

    def generate(self, request: Dict) -> Dict:
        """Return a decision dict with `decision` and `rationale`."""
        # request would include applicant data; here we return a sample
        applicant = request.get("applicant", {})
        # Simple rule: if flagged value triggers, deny; else approve
        if applicant.get("credit_score", 0) < 600:
            return {"decision": "deny", "rationale": "Low credit score"}
        return {"decision": "approve", "rationale": "Meets score threshold"}
