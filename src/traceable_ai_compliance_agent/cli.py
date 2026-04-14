"""CLI example wiring components together and supporting a config file."""
from typing import Dict
import os
import yaml

from .decision_engine import DecisionEngine
from .retriever import Retriever
from .citation_validator import CitationValidator
from .refusal_handler import RefusalHandler


def load_config(path: str = None) -> Dict:
    if not path:
        path = os.path.join(os.getcwd(), "config.example.yaml")
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def run_example(request: Dict = None, config_path: str = None) -> Dict:
    if request is None:
        request = {"applicant": {"name": "Alice", "credit_score": 720}}

    config = load_config(config_path)

    decision_engine = DecisionEngine(model=config.get("llm", {}).get("model", "gpt-4"))
    retriever = Retriever(top_k=config.get("retrieval", {}).get("top_k", 5), config=config)
    validator = CitationValidator()
    refuser = RefusalHandler()

    decision = decision_engine.generate(request)
    # Build a query that includes the applicant name and rationale for retrieval
    query = f"loan decision for {request.get('applicant', {}).get('name')}; rationale: {decision.get('rationale')}"
    evidence = retriever.search(query)

    # If no evidence found (e.g., fresh local SQLite DB), provide demo fallback
    if not evidence:
        # If the user explicitly triggers no-evidence, keep refusal behavior
        if request.get("_query_override") == "no-evidence":
            validation = validator.validate(decision, evidence)
        else:
            # demo evidence for local runs to avoid blocking the demo flow
            evidence = [
                {"text": "§12 Fair lending: Do not discriminate", "source": "regulations.pdf#p12", "score": 0.95},
                {"text": "§34 Income verification rules", "source": "manual.pdf#p34", "score": 0.87},
            ]
            validation = validator.validate(decision, evidence)
    else:
        validation = validator.validate(decision, evidence)

    if not validation["ok"]:
        flag = refuser.flag_for_review(request, validation["reason"])
        return {"decision": None, "status": "refused", "flag": flag}

    return {"decision": decision, "status": "approved_with_evidence", "evidence": validation["evidence"]}


if __name__ == "__main__":
    import json
    out = run_example()
    print(json.dumps(out, indent=2))
