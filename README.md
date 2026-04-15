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

Vercel Deployment (FastAPI + frontend together)
- The project is configured to deploy as a Python serverless app via `api/index.py` and `vercel.json`.
- Before deploy, verify `requirements.txt` is up to date and includes all runtime dependencies.
- Deploy from project root:

```bash
npm i -g vercel
vercel --prod
```

- The deployed app serves:
	- frontend at `/`
	- static assets at `/static/*`
	- API at `/api/*`
- For demo deployments on serverless environments, enable temporary in-memory persistence:

```bash
DEMO_MEMORY_FALLBACK=1
```

- In this mode, review queue and audit events are stored in process memory only (not persisted across cold starts).

- If you redeploy from Vercel dashboard, set project root to this repository root and keep `vercel.json` enabled.

Windows one-command runner
- From PowerShell at project root, run:

```powershell
./run_all.ps1
```

- This script will:
	- create `.venv` if missing,
	- install dependencies,
	- ingest sample docs,
	- run `pytest` smoke/API tests and `tools/run_e2e_smoke.py`,
	- start the API server (which serves the frontend at `/`).

- Optional flags:
	- `./run_all.ps1 -NoStart` (run setup + tests only)
	- `./run_all.ps1 -SkipTests`
	- `./run_all.ps1 -SkipInstall`
	- `./run_all.ps1 -Port 8010`

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
