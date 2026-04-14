from typing import List, Dict, Optional
from .vectorstore import FAISSVectorStore
from .embeddings import Embeddings
from .vectorstore_sqlite import SQLiteVectorStore


class Retriever:
    """Retriever that can use a FAISS vector store (via LangChain) or fall back to a stub.

    Config (optional): {'vector_store': 'faiss', 'storage': {'index_path': ...}, 'llm': {'provider': ..., 'embedding_model': ...}}
    """

    def __init__(self, top_k: int = 5, config: Optional[Dict] = None):
        self.top_k = top_k
        self.config = config or {}
        self.vs = None
        # initialize vector store if requested
        storage = self.config.get("storage", {})
        store_type = self.config.get("vector_store", self.config.get("storage", {}).get("vector_store", "faiss"))
        llm_cfg = self.config.get("llm", {})
        emb_provider = llm_cfg.get("provider", "openai")
        emb_model = llm_cfg.get("embedding_model", llm_cfg.get("model", "text-embedding-3-small"))
        embeddings = Embeddings(provider=emb_provider, model=emb_model)

        if store_type == "faiss":
            index_path = storage.get("index_path")
            self.vs = FAISSVectorStore(embeddings, index_path=index_path)
        elif store_type == "sqlite" or store_type == "local":
            db_path = storage.get("sqlite_db") or storage.get("index_path")
            self.vs = SQLiteVectorStore(db_path, embeddings=embeddings)
        else:
            # default to FAISS fallback
            index_path = storage.get("index_path")
            self.vs = FAISSVectorStore(embeddings, index_path=index_path)

    def search(self, query: str) -> List[Dict[str, object]]:
        """Return a list of evidence dicts with keys: text, source, score."""
        if self.vs is not None:
            return self.vs.similarity_search(query, k=self.top_k)

        # fallback deterministic stub
        if "no-evidence" in query:
            return []
        return [
            {"text": "§12 Fair lending: Do not discriminate", "source": "regulations.pdf#p12", "score": 0.95},
            {"text": "§34 Income verification rules", "source": "manual.pdf#p34", "score": 0.87},
        ][: self.top_k]
