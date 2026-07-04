def chunk_text(text, chunk_size=700, overlap=100):
    # If overlap were >= chunk_size, "start" would never move forward
    # and this would loop forever. Guard against that misconfiguration.
    assert overlap < chunk_size, "overlap must be smaller than chunk_size"

    # How far to slide forward for each new chunk. e.g. 700 - 100 = 600,
    # so each chunk repeats the last 100 characters of the previous one.
    step = chunk_size - overlap

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])

        # If this chunk already reached the end of the text, stop —
        # otherwise we'd keep looping and appending empty/duplicate chunks.
        if end >= len(text):
            break

        start += step

    return chunks


if __name__ == "__main__":
    # Quick end-to-end check: extract a real PDF's text, then chunk it,
    # so you can see Step 1 working start to finish.
    import sys

    from extract import extract_text_from_pdf

    path = sys.argv[1]
    text = extract_text_from_pdf(path)
    chunks = chunk_text(text)

    print(f"{len(chunks)} chunks")
    print("--- first chunk ---")
    print(chunks[0])
