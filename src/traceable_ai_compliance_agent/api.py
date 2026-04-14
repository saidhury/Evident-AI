import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .decision_engine import DecisionEngine
from .retriever import Retriever
from .citation_validator import CitationValidator
from .refusal_handler import RefusalHandler
from typing import Dict
import yaml

app = FastAPI(title="Traceable AI Compliance Agent")

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


@app.post("/api/decide")
async def decide(request: Request):
    payload = await request.json()
    config_path = os.path.join(os.getcwd(), "config.example.yaml")
    # load config if present so retriever uses selected vector store
    try:
        with open(config_path, "r") as f:
            config: Dict = yaml.safe_load(f) or {}
    except Exception:
        config = {}

    # wire components
    decision_engine = DecisionEngine()
    retriever = Retriever(top_k=config.get("retrieval", {}).get("top_k", 5), config=config)
    validator = CitationValidator()
    refuser = RefusalHandler()

    decision = decision_engine.generate(payload)
    query = f"loan decision for {payload.get('applicant', {}).get('name')}; rationale: {decision.get('rationale')}"
    evidence = retriever.search(query)
    validation = validator.validate(decision, evidence)

    if not validation["ok"]:
        flag = refuser.flag_for_review(payload, validation["reason"])
        return JSONResponse({"decision": None, "status": "refused", "flag": flag})

    return JSONResponse({"decision": decision, "status": "approved_with_evidence", "evidence": validation["evidence"]})
