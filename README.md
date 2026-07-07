# Silo
A private, offline AI assistant that lets you talk to your own files (like textbooks, notes, or contracts)

100% local RAG (Retrieval-Augmented Generation): documents are chunked, embedded, and stored in ChromaDB, then Gemma 4 answers questions grounded strictly in what was retrieved. No cloud services involved.

## Prerequisites

- **Docker Desktop** (with the WSL2/Linux engine on Windows)
- **Ollama** installed and running on the host machine (not in a container, so it can use your GPU)
- Two Ollama models pulled:

```
ollama pull gemma4
ollama pull nomic-embed-text
```

## Setup

Clone the repo, then from the project root:

```
docker compose up --build -d
```

This builds and starts three containers:

| Service | Purpose | Host port |
|---|---|---|
| `ingestion` | PDF upload + processing (`POST /ingest`) | `8001` |
| `chat` | Retrieval + LLM chat (`POST /chat`) | `8002` |
| `chroma` | Vector database | not exposed to host |

The `ingestion` and `chat` containers reach Ollama on your host via `http://host.docker.internal:11434`. Make sure Ollama is running before starting the stack.

## Usage

**Upload a document:**

```
curl.exe -F "file=@C:/path/to/your.pdf" http://localhost:8001/ingest
```

Returns `{"filename": ..., "status": "stored" | "duplicate", "chunks_stored": N}`. Re-uploading the same file is a no-op (deduplicated by content hash).

**Ask a question:**

```powershell
Invoke-RestMethod -Uri http://localhost:8002/chat -Method Post -ContentType "application/json" -Body '{"query": "your question here"}'
```

(In bash/Git Bash, use `curl -N -X POST http://localhost:8002/chat -H "Content-Type: application/json" -d '{"query": "your question here"}'` instead — PowerShell's native argument passing to `curl.exe` mangles embedded quotes, so `Invoke-RestMethod` is the reliable option there.)

Returns a plain-text answer grounded only in your uploaded documents. Conversation history persists across requests (in `chat/app/chat_history.json`) and a sliding window of recent turns is replayed to the model each time, so context never grows unbounded.

## Stopping / resetting

```
docker compose down
```

Stops and removes all containers. Your uploaded vectors are safe — ChromaDB's data is bind-mounted to `./chroma_data` on the host, so it survives resets. To wipe all stored data, delete that folder manually.

## Architecture

```
ingestion/   PDF extraction, chunking, embedding, storage (Steps 1-3, 6)
chat/        Retrieval, context injection, LLM chat (Steps 4-6)
chroma/      Standalone ChromaDB server (official image, Step 7)
docker-compose.yml   Links all three services (Steps 7-8)
```

See `ingestion/README.md` and `chat/README.md` for service-specific details.
