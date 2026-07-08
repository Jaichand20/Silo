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
| `ui` | Static HTML/CSS/JS interface (upload + chat) | `8501` |
| `ingestion` | PDF upload + processing (`POST /ingest`) | `8001` |
| `chat` | Retrieval + LLM chat (`POST /chat`) | `8002` |
| `chroma` | Vector database | not exposed to host |

The `ingestion` and `chat` containers reach Ollama on your host via `http://host.docker.internal:11434`. Make sure Ollama is running before starting the stack.

## Usage

Open **http://localhost:8501** in your browser. Use "+ New Chat" in the sidebar to start an isolated conversation — each chat has its own document pool, so uploads and questions never leak between chats. Drop PDFs into the Sources panel on the right (one or several at once), then ask questions in the chat box — answers stream in live and are grounded only in the documents uploaded to that chat. Switch between chats or delete one from the sidebar (a confirmation prompt appears unless you've dismissed it for the session). Conversation history and uploaded documents persist per chat across page reloads and container restarts.

### Advanced: raw REST API

The UI is just a client of the ingestion and chat services — you can call them directly instead. Every call takes a `chat_id` (any string you choose) to scope it to a specific conversation.

```
curl.exe -F "files=@C:/path/to/your.pdf" -F "chat_id=my-chat" http://localhost:8001/ingest
```

Accepts one or more `files` fields in the same request. Returns `{"results": [{"filename": ..., "status": "stored" | "duplicate", "chunks_stored": N}, ...]}`. Re-uploading the same file to the same chat is a no-op (deduplicated by content hash, per chat).

Other ingestion endpoints: `GET /documents?chat_id=` (list documents in a chat), `DELETE /documents?chat_id=&doc_hash=` (remove one document), `DELETE /chats/{chat_id}` (wipe a chat's documents/vectors).

```powershell
Invoke-RestMethod -Uri http://localhost:8002/chat -Method Post -ContentType "application/json" -Body '{"query": "your question here", "chat_id": "my-chat"}'
```

(In bash/Git Bash, use `curl -N -X POST http://localhost:8002/chat -H "Content-Type: application/json" -d '{"query": "your question here", "chat_id": "my-chat"}'` instead — PowerShell's native argument passing to `curl.exe` mangles embedded quotes, so `Invoke-RestMethod` is the reliable option there.)

Other chat endpoints: `GET /chats` (list known chat IDs), `GET /history?chat_id=` (a chat's message history), `DELETE /chats/{chat_id}` (wipe a chat's history).

## Stopping / resetting

```
docker compose down
```

Stops and removes all containers. Your uploaded vectors are safe — ChromaDB's data is bind-mounted to `./chroma_data` on the host, so it survives resets. To wipe all stored data, delete that folder manually.

## Architecture

```
ingestion/   PDF extraction, chunking, embedding, storage, per-chat documents (Steps 1-3, 6, 10)
chat/        Retrieval, context injection, LLM chat, per-chat history (Steps 4-6, 10)
chroma/      Standalone ChromaDB server (official image, Step 7)
ui/          Static HTML/CSS/JS interface (Steps 9-10)
docker-compose.yml   Links all four services (Steps 7-9)
```

Each chat gets its own ChromaDB collection, dedup tracking, and history file, so retrieval is structurally isolated per conversation rather than relying on query-time filtering (Step 10).

See `ingestion/README.md`, `chat/README.md`, and `ui/README.md` for service-specific details.
