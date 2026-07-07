import os

import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


def get_embedding(text, model="nomic-embed-text"):
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": model, "prompt": text},
    )
    response.raise_for_status()

    return response.json()["embedding"]


if __name__ == "__main__":
    import sys

    text = sys.argv[1]
    vector = get_embedding(text)

    print(f"Vector length: {len(vector)}")
    print(vector[:5], "...")
