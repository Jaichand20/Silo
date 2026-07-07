import os

import chromadb
from chromadb.config import Settings

CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))


def get_collection():
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection("documents")


def store_chunks(chunks, embeddings, doc_hash, source_path):
    collection = get_collection()

    ids = [f"{doc_hash}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"source": source_path, "chunk_index": i} for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )


def process_document(pdf_path):
    from dedupe import hash_file, is_duplicate, mark_as_seen
    from extract import extract_text_from_pdf
    from chunk import chunk_text
    from embed import get_embedding

    doc_hash = hash_file(pdf_path)
    if is_duplicate(doc_hash):
        print("Already ingested, skipping.")
        return {"status": "duplicate", "chunks_stored": 0}

    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    embeddings = [get_embedding(chunk) for chunk in chunks]

    store_chunks(chunks, embeddings, doc_hash, pdf_path)
    mark_as_seen(doc_hash)

    print(f"Stored {len(chunks)} chunks from {pdf_path}.")
    return {"status": "stored", "chunks_stored": len(chunks)}


if __name__ == "__main__":
    import sys

    process_document(sys.argv[1])
