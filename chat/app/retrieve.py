import os

import chromadb
import requests
from chromadb.config import Settings

# Same defaults/pattern as ingestion/app/embed.py and store.py — kept
# duplicated here rather than imported across services, since Step 6
# splits ingestion and chat into independent services that shouldn't
# share code directly.
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

    # Chroma takes a list of query vectors (so it can batch multiple
    # queries at once) — we only ever send one, so we read back index 0.
    results = collection.query(query_embeddings=[query_vector], n_results=top_k)
    return results["documents"][0]


if __name__ == "__main__":
    import sys

    # Windows terminals default to a legacy codepage (cp1252) that can't
    # print many characters PDFs commonly contain (bullets, smart quotes,
    # em-dashes). Force stdout to UTF-8 so printing chunks never crashes.
    sys.stdout.reconfigure(encoding="utf-8")

    query = sys.argv[1]
    chunks = retrieve_top_chunks(query)

    for i, chunk in enumerate(chunks, start=1):
        print(f"--- chunk {i} ---")
        print(chunk)
