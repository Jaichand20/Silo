def chunk_text(text, chunk_size=700, overlap=100):
    assert overlap < chunk_size, "overlap must be smaller than chunk_size"

    step = chunk_size - overlap

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])

        if end >= len(text):
            break

        start += step

    return chunks


if __name__ == "__main__":
    import sys

    from extract import extract_text_from_pdf

    path = sys.argv[1]
    text = extract_text_from_pdf(path)
    chunks = chunk_text(text)

    print(f"{len(chunks)} chunks")
    print("--- first chunk ---")
    print(chunks[0])
