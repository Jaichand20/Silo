# Chat Service

Handles Steps 4-5 of the plan: vector retrieval against ChromaDB and
context-injected chat via Ollama's `/api/chat`. Independent FastAPI
service (Step 6), communicates with the ingestion service only over
REST.
