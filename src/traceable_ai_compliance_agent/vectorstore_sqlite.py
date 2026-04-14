import sqlite3
import os
import pickle
from typing import List, Dict, Optional
import numpy as np


class SQLiteVectorStore:
    """A minimal, dependency-light local vector store using SQLite.

    Stores documents and pickled embeddings. Good for local debugging and
    simple to switch to from config.
    """

    def __init__(self, db_path: Optional[str] = None, embeddings=None):
        self.db_path = db_path or os.path.join(os.getcwd(), "data", "vectors.db")
        self.embeddings = embeddings
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._ensure_table()

    def _ensure_table(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                text TEXT,
                source TEXT,
                embedding BLOB
            )
            """
        )
        self.conn.commit()

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None):
        metadatas = metadatas or [{}] * len(texts)
        cur = self.conn.cursor()
        # compute embeddings (batch)
        if self.embeddings is None:
            raise RuntimeError("Embeddings implementation required for SQLiteVectorStore")
        vecs = self.embeddings.embed_documents(texts)
        for i, (text, meta) in enumerate(zip(texts, metadatas)):
            emb = pickle.dumps(np.array(vecs[i], dtype=np.float32))
            doc_id = meta.get("id") or f"doc-{i}"
            source = meta.get("source") or "local"
            cur.execute(
                "REPLACE INTO documents (id, text, source, embedding) VALUES (?, ?, ?, ?)",
                (doc_id, text, source, emb),
            )
        self.conn.commit()
        return True

    def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        # compute query embedding
        qvec = self.embeddings.embed_documents([query])[0]
        qv = np.array(qvec, dtype=np.float32)
        cur = self.conn.cursor()
        cur.execute("SELECT id, text, source, embedding FROM documents")
        rows = cur.fetchall()
        results = []
        for id_, text, source, emb_blob in rows:
            try:
                emb = pickle.loads(emb_blob)
                emb = emb.astype(np.float32)
                # cosine similarity
                num = float(np.dot(qv, emb))
                den = float(np.linalg.norm(qv) * np.linalg.norm(emb) + 1e-12)
                score = num / den
            except Exception:
                score = 0.0
            results.append({"id": id_, "text": text, "source": source, "score": score})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:k]
