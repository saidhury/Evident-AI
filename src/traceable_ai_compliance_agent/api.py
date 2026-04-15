import os
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .decision_engine import DecisionEngine
from .retriever import Retriever
from .citation_validator import CitationValidator
from .refusal_handler import RefusalHandler
from .policy_engine import PolicyEngine
from .audit_logger import AuditLogger
from .review_queue import ReviewQueue
from .pii import mask_pii
from typing import Dict
import yaml

app = FastAPI(title="Traceable AI Compliance Agent")


def _resolve_memory_fallback() -> bool:
    explicit = os.getenv("DEMO_MEMORY_FALLBACK")
    if explicit is not None:
        return explicit.strip().lower() in {"1", "true", "yes", "on"}
    return bool(os.getenv("VERCEL"))


memory_fallback_mode = _resolve_memory_fallback()
review_queue = ReviewQueue(use_memory=memory_fallback_mode)
audit_logger = AuditLogger(use_memory=memory_fallback_mode)


def _extract_role(request: Request) -> str:
    return (request.headers.get("X-Reviewer-Role") or "").strip().lower()


def _extract_reviewer(request: Request, fallback: str = "analyst") -> str:
    return (request.headers.get("X-Reviewer-Id") or fallback).strip()


def _rbac_forbidden(role: str, allowed_roles):
    if role in allowed_roles:
        return None
    return JSONResponse(
        {
            "error": "forbidden",
            "message": f"Role '{role or 'none'}' not allowed for this endpoint",
            "allowed_roles": sorted(list(allowed_roles)),
        },
        status_code=403,
    )

# mount frontend static directory at /static and serve index at root
frontend_dir = os.path.join(os.getcwd(), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="frontend_static")


@app.get("/")
async def root():
    index = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index):
        return HTMLResponse(open(index, "r").read())
    return HTMLResponse("<html><body><h1>Traceable AI Compliance Agent</h1></body></html>")


@app.get("/api/review/queue")
async def get_review_queue(request: Request, status: str = None):
    role = _extract_role(request)
    denied = _rbac_forbidden(role, {"analyst", "reviewer", "admin"})
    if denied:
        return denied
    return JSONResponse({"items": review_queue.list_tickets(status=status)})


@app.get("/api/review/queue/export")
async def export_review_queue(request: Request, status: str = None):
    role = _extract_role(request)
    denied = _rbac_forbidden(role, {"reviewer", "admin"})
    if denied:
        return denied
    return JSONResponse(review_queue.export_payload(status=status))


@app.post("/api/review/{ticket_id}/action")
async def review_action(ticket_id: str, request: Request):
    role = _extract_role(request)
    denied = _rbac_forbidden(role, {"reviewer", "admin"})
    if denied:
        return denied

    payload = await request.json()
    action = payload.get("action", "comment")
    reviewer = payload.get("reviewer", _extract_reviewer(request, fallback="reviewer"))
    notes = payload.get("notes", "")

    updated = review_queue.apply_action(ticket_id=ticket_id, action=action, reviewer=reviewer, notes=notes)
    if not updated:
        return JSONResponse({"error": "ticket_not_found", "ticket_id": ticket_id}, status_code=404)

    audit_logger.log_event(
        "review_action",
        {
            "ticket_id": ticket_id,
            "action": action,
            "reviewer": reviewer,
            "notes": notes,
            "status": updated.get("status"),
            "role": role,
        },
    )
    return JSONResponse({"ticket": updated})


@app.post("/api/decide")
async def decide(request: Request):
    payload = await request.json()
    trace_id = str(uuid4())
    config_path = os.path.join(os.getcwd(), "config.example.yaml")
    # load config if present so retriever uses selected vector store
    try:
        with open(config_path, "r") as f:
            config: Dict = yaml.safe_load(f) or {}
    except Exception:
        config = {}

    # wire components
    decision_engine = DecisionEngine()
    policy_engine = PolicyEngine(config=config)
    retriever = Retriever(top_k=config.get("retrieval", {}).get("top_k", 5), config=config)
    validator = CitationValidator()
    refuser = RefusalHandler(review_queue=review_queue)

    min_evidence_score = config.get("retrieval", {}).get("min_evidence_score", 0.2)

    decision = decision_engine.generate(payload)
    policy_result = policy_engine.evaluate(payload)
    if not policy_result.ok:
        decision = {
            "decision": "deny",
            "rationale": policy_result.reason,
            "policy_rule": policy_result.rule_id,
        }

    query = f"loan decision for {payload.get('applicant', {}).get('name')}; rationale: {decision.get('rationale')}"
    evidence = retriever.search(query)
    validation = validator.validate(decision, evidence, min_evidence_score=min_evidence_score)
    counterfactual = policy_engine.counterfactual(payload)

    base_meta = {
        "trace_id": trace_id,
        "policy_version": policy_engine.version,
        "config_fingerprint": policy_engine.config_fingerprint(),
        "evidence_quality": validation.get("evidence_quality", 0.0),
        "counterfactual": counterfactual,
    }

    if not validation["ok"]:
        flag = refuser.flag_for_review(payload, validation["reason"], trace_id=trace_id)
        response = {"decision": None, "status": "refused", "flag": flag, "meta": base_meta}
        audit_logger.log_event(
            "decision_refused",
            {
                "trace_id": trace_id,
                "request": mask_pii(payload),
                "decision": decision,
                "reason": validation["reason"],
                "flag": flag,
                "meta": base_meta,
            },
        )
        return JSONResponse(response)

    response = {
        "decision": decision,
        "status": "approved_with_evidence",
        "evidence": validation["evidence"],
        "meta": base_meta,
    }
    audit_logger.log_event(
        "decision_approved",
        {
            "trace_id": trace_id,
            "request": mask_pii(payload),
            "decision": decision,
            "evidence_count": len(validation.get("evidence", [])),
            "meta": base_meta,
        },
    )
    return JSONResponse(response)
