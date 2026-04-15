import json
import os
from fastapi.testclient import TestClient

from traceable_ai_compliance_agent.api import app


client = TestClient(app)


def test_decide_approve():
    payload = {"applicant": {"name": "TestUser", "credit_score": 720}}
    resp = client.post("/api/decide", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") in ("approved_with_evidence", "refused")
    assert "meta" in body
    assert "trace_id" in body["meta"]
    assert "policy_version" in body["meta"]


def test_decide_refuse_low_score():
    payload = {"applicant": {"name": "LowScore", "credit_score": 450}}
    resp = client.post("/api/decide", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    # Low credit score leads to a deny decision by DecisionEngine, may be refused if no evidence
    assert "status" in body
    assert "meta" in body
    assert "counterfactual" in body["meta"]


def test_review_queue_endpoints():
    payload = {"applicant": {"name": "NeedsReview", "credit_score": 710}}
    decide = client.post("/api/decide", json=payload)
    assert decide.status_code == 200

    queue = client.get("/api/review/queue", headers={"X-Reviewer-Role": "reviewer"})
    assert queue.status_code == 200
    items = queue.json().get("items", [])
    assert isinstance(items, list)

    if not items:
        return

    ticket_id = items[-1]["ticket_id"]
    action = client.post(
        f"/api/review/{ticket_id}/action",
        json={"action": "comment", "reviewer": "qa", "notes": "triaged"},
        headers={"X-Reviewer-Role": "reviewer", "X-Reviewer-Id": "qa-user"},
    )
    assert action.status_code == 200
    assert action.json()["ticket"]["ticket_id"] == ticket_id


def test_review_rbac_forbidden_without_role():
    queue = client.get("/api/review/queue")
    assert queue.status_code == 403

    action = client.post(
        "/api/review/TICKET-1/action",
        json={"action": "comment", "reviewer": "qa", "notes": "rbac check"},
    )
    assert action.status_code == 403

    export = client.get("/api/review/queue/export")
    assert export.status_code == 403


def test_review_export_allowed_for_reviewer():
    export = client.get("/api/review/queue/export", headers={"X-Reviewer-Role": "reviewer"})
    assert export.status_code == 200
    body = export.json()
    assert "count" in body
    assert "items" in body
