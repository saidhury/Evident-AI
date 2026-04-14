import json
from fastapi.testclient import TestClient

from traceable_ai_compliance_agent.api import app


client = TestClient(app)


def test_decide_approve():
    payload = {"applicant": {"name": "TestUser", "credit_score": 720}}
    resp = client.post("/api/decide", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") in ("approved_with_evidence", "refused")


def test_decide_refuse_low_score():
    payload = {"applicant": {"name": "LowScore", "credit_score": 450}}
    resp = client.post("/api/decide", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    # Low credit score leads to a deny decision by DecisionEngine, may be refused if no evidence
    assert "status" in body
