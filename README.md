# Traceable AI Compliance Agent

Enterprise-grade, auditable AI co-pilot for the banking & financial sector.

Overview
- Evidence-first decision engine + paragraph-level citation validator.
- Refusal-first policy when no valid evidence is found.

Quickstart
1. Create a venv: `python -m venv .venv && source .venv/bin/activate`
2. Install: `pip install -r requirements.txt`
3. Ingest sample docs: `python -m traceable_ai_compliance_agent.ingest_cli`
4. Run server (from project root):

```bash
PYTHONPATH=src uvicorn traceable_ai_compliance_agent.api:app --reload --host 0.0.0.0 --port 8000
```

5. Open `http://127.0.0.1:8000/` to view the frontend.

Switching embedding provider to Gemini (example)
- Implement a small internal HTTP wrapper that calls Google Gemini / Vertex AI with your org credentials
- Set these environment variables (or put them in `.env`):

```bash
export GEMINI_EMBEDDING_URL="https://your-internal-host/gemini/embed"
export GEMINI_API_KEY="your_gemini_key"
```

- Update `config.example.yaml` to set `llm.provider: gemini` and restart the app. The app will POST `{"inputs": [..]}` to `GEMINI_EMBEDDING_URL` and expects `{"embeddings": [[...], ...]}` in response. The wrapper gives you control over private keys and routing inside your firewall.

Using the offline SQLite fallback vector DB (debugging)
- The project includes a local SQLite vector store. To use it, set `storage.vector_store: sqlite` in `config.example.yaml` (this is the default in the example).
- The default DB file is `./data/vectors.db`. To ingest sample docs into the local DB:

```bash
PYTHONPATH=src python -m traceable_ai_compliance_agent.ingest_cli
```

Then run the server:

```bash
PYTHONPATH=src uvicorn traceable_ai_compliance_agent.api:app --reload --port 8000
```

Notes
- The `Embeddings` wrapper will use OpenAI (via LangChain) when `OPENAI_API_KEY` is present and `llm.provider` is `openai`.
- For `gemini`, the code expects an HTTP endpoint in `GEMINI_EMBEDDING_URL` that returns embeddings for a batch of inputs. This design keeps secrets and network access inside your infrastructure.
- The SQLite store uses pickled numpy arrays for embeddings and performs a simple cosine similarity. It's intended for local debugging, not large-scale production.

Files
- `src/traceable_ai_compliance_agent/` — core stubs and CLI
- `config.example.yaml` — example config
- `requirements.txt` — runtime deps (placeholder)

Next steps
- Wire LangChain, vector DB (Pinecone/FAISS), and an LLM provider.
