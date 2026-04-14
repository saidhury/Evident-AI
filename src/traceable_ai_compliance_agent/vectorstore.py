from typing import List, Dict, Optional
import os
import pickle

try:
    from langchain.vectorstores import FAISS
    from langchain.docstore.document import Document
except Exception:
    FAISS = None
    Document = None


class FAISSVectorStore:
    """Simple FAISS-backed vector store wrapper with disk persistence.

    Falls back to a naive in-memory list when LangChain/FAISS is unavailable.
    """

    def __init__(self, embeddings, index_path: Optional[str] = None):
        self.embeddings = embeddings
        self.index_path = index_path
        self.store = None
        if index_path and os.path.exists(index_path):
            try:
                with open(index_path, "rb") as f:
                    self.store = pickle.load(f)
            except Exception:
                self.store = None

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None):
        metadatas = metadatas or [{}] * len(texts)
        if FAISS is not None and self.embeddings is not None and getattr(self.embeddings, "impl", None) is not None:
            docs = [Document(page_content=t, metadata=m) for t, m in zip(texts, metadatas)]
            self.store = FAISS.from_documents(docs, self.embeddings.impl)
            if self.index_path:
                with open(self.index_path, "wb") as f:
                    pickle.dump(self.store, f)
            return True

        # fallback: simple list store
        self.store = list(zip(texts, metadatas))
        return True

    def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        if FAISS is not None and self.store is not None and hasattr(self.store, "similarity_search"):
            docs = self.store.similarity_search(query, k=k)
            return [{"text": d.page_content, "source": d.metadata.get("source"), "score": None} for d in docs]

        # fallback: substring match ranked by simple heuristic
        res = []
        for text, meta in (self.store or []):
            if query.lower() in text.lower():
                res.append({"text": text, "source": meta.get("source"), "score": 1.0})
            if len(res) >= k:
                break
        return res
