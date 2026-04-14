import os
from typing import List
import json

try:
    from langchain.embeddings import OpenAIEmbeddings
except Exception:
    OpenAIEmbeddings = None

import requests


class Embeddings:
    """Wrapper for embeddings provider with several backends and safe fallback.

    Supported providers:
    - 'openai': uses LangChain's `OpenAIEmbeddings` when `OPENAI_API_KEY` is set
    - 'gemini': if `GEMINI_EMBEDDING_URL` and `GEMINI_API_KEY` are set, the class will POST
       to that URL and expect a JSON response with an `embedding` array for each input.
    - fallback: deterministic hash-based small vector for offline debugging
    """

    def __init__(self, provider: str = "openai", model: str = "text-embedding-3-small"):
        self.provider = provider
        self.model = model
        self.impl = None
        # OpenAI via LangChain
        if provider == "openai" and OpenAIEmbeddings is not None:
            key = os.getenv("OPENAI_API_KEY")
            if key:
                self.impl = ("openai", OpenAIEmbeddings(model=model, openai_api_key=key))

        # Gemini via a configurable HTTP embedding endpoint (user-provided wrapper)
        if provider == "gemini":
            gem_url = os.getenv("GEMINI_EMBEDDING_URL")
            gem_key = os.getenv("GEMINI_API_KEY")
            if gem_url and gem_key:
                self.impl = ("gemini", {"url": gem_url, "key": gem_key})

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.impl:
            kind = self.impl[0]
            if kind == "openai":
                return self.impl[1].embed_documents(texts)
            if kind == "gemini":
                cfg = self.impl[1]
                # Expect the GEMINI endpoint to accept JSON {"inputs": [str,...]} and
                # return JSON {"embeddings": [[...],[...]]} or similar. This is intentionally
                # generic — adapt the request/response parsing to your Gemini wrapper.
                headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
                try:
                    resp = requests.post(cfg["url"], headers=headers, json={"inputs": texts}, timeout=20)
                    resp.raise_for_status()
                    payload = resp.json()
                    # Try several common shapes
                    if isinstance(payload.get("embeddings"), list):
                        return payload["embeddings"]
                    if isinstance(payload.get("data"), list):
                        # some Gemini wrappers return {'data': [{'embedding': [...]}, ...]}
                        out = []
                        for item in payload["data"]:
                            if isinstance(item, dict) and item.get("embedding"):
                                out.append(item["embedding"])
                        if out:
                            return out
                except Exception:
                    # fall through to fallback
                    pass

        return [self._fake_embedding(t) for t in texts]

    def _fake_embedding(self, text: str) -> List[float]:
        import hashlib

        h = hashlib.sha256(text.encode("utf-8")).digest()
        return [b / 255.0 for b in h[:64]]
