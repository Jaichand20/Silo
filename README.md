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

This builds and starts four containers:

| Service | Purpose | Host port |
|---|---|---|
| `ui` | Streamlit interface (upload + chat) | `8501` |
| `ingestion` | PDF upload + processing (`POST /ingest`) | `8001` |
| `chat` | Retrieval + LLM chat (`POST /chat`) | `8002` |
| `chroma` | Vector database | not exposed to host |

The `ingestion` and `chat` containers reach Ollama on your host via `http://host.docker.internal:11434`. Make sure Ollama is running before starting the stack.

## Usage

Open **http://localhost:8501** in your browser. Upload a PDF, then ask questions about it in the chat box — answers stream in live and are grounded only in what you've uploaded. Conversation history persists across page reloads and a sliding window of recent turns is replayed to the model each time, so context never grows unbounded.

### Advanced: raw REST API

The UI is just a client of the ingestion and chat services — you can call them directly instead:

```
curl.exe -F "file=@C:/path/to/your.pdf" http://localhost:8001/ingest
```

Returns `{"filename": ..., "status": "stored" | "duplicate", "chunks_stored": N}`. Re-uploading the same file is a no-op (deduplicated by content hash).

```powershell
Invoke-RestMethod -Uri http://localhost:8002/chat -Method Post -ContentType "application/json" -Body '{"query": "your question here"}'
```

(In bash/Git Bash, use `curl -N -X POST http://localhost:8002/chat -H "Content-Type: application/json" -d '{"query": "your question here"}'` instead — PowerShell's native argument passing to `curl.exe` mangles embedded quotes, so `Invoke-RestMethod` is the reliable option there.)

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
ui/          Streamlit interface (Step 9)
docker-compose.yml   Links all four services (Steps 7-9)
```

See `ingestion/README.md`, `chat/README.md`, and `ui/README.md` for service-specific details.
