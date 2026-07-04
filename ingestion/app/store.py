import chromadb

# Where ChromaDB writes its files to disk. Step 8 will bind-mount this
# folder as a Docker volume so it survives container restarts.
CHROMA_PATH = "chroma_data"


def get_collection():
    # PersistentClient saves everything to CHROMA_PATH instead of only
    # keeping it in memory, so data survives between runs.
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # get_or_create means this is safe to call every time — it won't
    # error out just because the collection already exists from a
    # previous run.
    return client.get_or_create_collection("documents")


def store_chunks(chunks, embeddings, doc_hash, source_path):
    collection = get_collection()

    # Chunk IDs are built from the document hash + position, so the same
    # document always produces the same IDs — re-storing overwrites the
    # same rows instead of creating duplicates.
    ids = [f"{doc_hash}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"source": source_path, "chunk_index": i} for i in range(len(chunks))
    ]

    # upsert = "insert or update": if an ID already exists it gets
    # overwritten instead of raising an error, which add() would do.
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )


def process_document(pdf_path):
    # Imported here (not at the top) since these are our own Step 1/2
    # modules, kept next to this file rather than installed packages.
    from dedupe import hash_file, is_duplicate, mark_as_seen
    from extract import extract_text_from_pdf
    from chunk import chunk_text
    from embed import get_embedding

    doc_hash = hash_file(pdf_path)
    if is_duplicate(doc_hash):
        print("Already ingested, skipping.")
        return

    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    embeddings = [get_embedding(chunk) for chunk in chunks]

    store_chunks(chunks, embeddings, doc_hash, pdf_path)
    mark_as_seen(doc_hash)

    print(f"Stored {len(chunks)} chunks from {pdf_path}.")


if __name__ == "__main__":
    import sys

    process_document(sys.argv[1])
