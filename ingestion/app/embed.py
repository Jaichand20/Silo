import os

import requests

# Read from an environment variable if set, otherwise default to localhost.
# Step 7 (Docker Compose) will set OLLAMA_URL to the container-networking
# address instead — this line is the one place that needs to change for that.
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


def get_embedding(text, model="nomic-embed-text"):
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": model, "prompt": text},
    )
    # Raises an error immediately if Ollama isn't running or the model
    # isn't pulled, instead of failing confusingly later on a missing key.
    response.raise_for_status()

    return response.json()["embedding"]


if __name__ == "__main__":
    import sys

    text = sys.argv[1]
    vector = get_embedding(text)

    print(f"Vector length: {len(vector)}")
    print(vector[:5], "...")
