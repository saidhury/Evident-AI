import json
import os
from typing import List

from .embeddings import Embeddings
from .vectorstore import FAISSVectorStore


def load_sample(path: str) -> List[dict]:
    with open(path, "r") as f:
        return json.load(f)


def ingest(path: str, index_path: str = None):
    docs = load_sample(path)
    texts = [d["text"] for d in docs]
    metadatas = [{"id": d.get("id"), "source": d.get("source"), "page": d.get("page")} for d in docs]
    embeddings = Embeddings()
    vs = FAISSVectorStore(embeddings, index_path=index_path)
    vs.add_documents(texts, metadatas=metadatas)
    print(f"Ingested {len(texts)} documents to index: {index_path}")


if __name__ == "__main__":
    cfg_path = os.path.join(os.getcwd(), "data", "sample_docs.json")
    index_path = os.path.join(os.getcwd(), "data", "faiss_index.pkl")
    ingest(cfg_path, index_path=index_path)
