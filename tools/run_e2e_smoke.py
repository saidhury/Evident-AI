"""End-to-end smoke script:
- ingests sample docs into SQLite vector DB
- runs the API TestClient against /api/decide and prints response

Usage: PYTHONPATH=src python tools/run_e2e_smoke.py
"""
import os
import json
from fastapi.testclient import TestClient

from traceable_ai_compliance_agent import ingest_cli
from traceable_ai_compliance_agent.api import app


def ensure_ingested():
    data_path = os.path.join(os.getcwd(), "data", "sample_docs.json")
    db_path = os.path.join(os.getcwd(), "data", "vectors.db")
    ingest_cli.ingest(data_path, index_path=db_path)


def run_test():
    ensure_ingested()
    client = TestClient(app)
    payload = {"applicant": {"name": "E2E Tester", "credit_score": 700}}
    resp = client.post("/api/decide", json=payload)
    print("status:", resp.status_code)
    print(json.dumps(resp.json(), indent=2))


if __name__ == "__main__":
    run_test()
