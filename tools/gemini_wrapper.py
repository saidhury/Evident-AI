"""Small local Gemini embedding wrapper for testing.

Run: `python tools/gemini_wrapper.py` — it starts a server on port 9000
POST /embed accepts JSON {"inputs": ["text", ...]} and returns
{"embeddings": [[...], ...]} where embeddings are deterministic vectors.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import hashlib

app = FastAPI(title="Local Gemini Wrapper (demo)")


def fake_embed(text: str):
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # produce 64-dim float list normalized to 0-1
    return [b / 255.0 for b in h[:64]]


@app.post("/embed")
async def embed(req: Request):
    payload = await req.json()
    inputs = payload.get("inputs") or payload.get("input") or []
    embeddings = [fake_embed(t) for t in inputs]
    return JSONResponse({"embeddings": embeddings})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9000)
