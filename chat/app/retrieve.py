import os

import chromadb
import requests
from chromadb.config import Settings

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
CHROMA_PATH = os.environ.get("CHROMA_PATH", "../../chroma_data")


def embed_query(text, model="nomic-embed-text"):
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": model, "prompt": text},
    )
    response.raise_for_status()
    return response.json()["embedding"]


def get_collection():
    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection("documents")


def retrieve_top_chunks(query, top_k=3):
    query_vector = embed_query(query)
    collection = get_collection()

    results = collection.query(query_embeddings=[query_vector], n_results=top_k)
    return results["documents"][0]


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    query = sys.argv[1]
    chunks = retrieve_top_chunks(query)

    for i, chunk in enumerate(chunks, start=1):
        print(f"--- chunk {i} ---")
        print(chunk)
