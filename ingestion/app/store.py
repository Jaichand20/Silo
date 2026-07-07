import os

import chromadb
from chromadb.config import Settings

CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))


def get_collection(chat_id):
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(f"chat_{chat_id}")


def store_chunks(chunks, embeddings, doc_hash, source_path, chat_id):
    collection = get_collection(chat_id)

    ids = [f"{doc_hash}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"source": source_path, "chunk_index": i, "doc_hash": doc_hash}
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )


def delete_document(chat_id, doc_hash):
    collection = get_collection(chat_id)
    collection.delete(where={"doc_hash": doc_hash})


def delete_chat(chat_id):
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        settings=Settings(anonymized_telemetry=False),
    )
    try:
        client.delete_collection(f"chat_{chat_id}")
    except Exception:
        pass


def process_document(pdf_path, chat_id):
    from dedupe import hash_file, is_duplicate, mark_as_seen
    from documents import add_document
    from extract import extract_text_from_pdf
    from chunk import chunk_text
    from embed import get_embedding

    seen_path = f"seen_hashes/{chat_id}.txt"

    doc_hash = hash_file(pdf_path)
    if is_duplicate(doc_hash, seen_path=seen_path):
        print("Already ingested, skipping.")
        return {"status": "duplicate", "chunks_stored": 0}

    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    embeddings = [get_embedding(chunk) for chunk in chunks]

    store_chunks(chunks, embeddings, doc_hash, pdf_path, chat_id)
    mark_as_seen(doc_hash, seen_path=seen_path)
    add_document(chat_id, doc_hash, os.path.basename(pdf_path))

    print(f"Stored {len(chunks)} chunks from {pdf_path}.")
    return {"status": "stored", "chunks_stored": len(chunks)}


if __name__ == "__main__":
    import sys

    process_document(sys.argv[1], sys.argv[2])
