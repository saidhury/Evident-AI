import os
from typing import List, Dict, Optional

try:
    import pinecone
except Exception:
    pinecone = None


class PineconeVectorStore:
    """Simple Pinecone wrapper for upsert and query.

    Falls back to raising an informative error if Pinecone client is not installed
    or environment variables are missing.
    """

    def __init__(self, index_name: str = None, api_key: str = None, environment: str = None):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENV")
        self.index_name = index_name or os.getenv("PINECONE_INDEX")
        self._index = None
        if pinecone is None:
            return
        if not self.api_key or not self.environment or not self.index_name:
            return
        pinecone.init(api_key=self.api_key, environment=self.environment)
        self._index = pinecone.Index(self.index_name)

    def upsert(self, vectors: List[Dict]):
        """Upsert vectors: list of {'id': str, 'values': List[float], 'metadata': dict}"""
        if self._index is None:
            raise RuntimeError("Pinecone client not initialized. Check PINECONE_API_KEY, PINECONE_ENV, and pinecone package.")
        self._index.upsert(vectors)

    def query(self, vector: List[float], top_k: int = 5) -> List[Dict]:
        if self._index is None:
            raise RuntimeError("Pinecone client not initialized.")
        res = self._index.query(vector=vector, top_k=top_k, include_metadata=True)
        out = []
        for match in res['matches']:
            out.append({
                'id': match['id'],
                'score': match['score'],
                'metadata': match.get('metadata')
            })
        return out
