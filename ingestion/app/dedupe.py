import hashlib


def hash_file(path):
    # Read the file's raw bytes and fingerprint them. Same bytes always
    # produce the same hash, no matter what the file is named.
    with open(path, "rb") as f:
        file_bytes = f.read()
    return hashlib.sha256(file_bytes).hexdigest()


def is_duplicate(file_hash, seen_path="seen_hashes.txt"):
    try:
        with open(seen_path, "r") as f:
            seen_hashes = f.read().splitlines()
    except FileNotFoundError:
        # No file yet means nothing has ever been ingested.
        return False

    return file_hash in seen_hashes


def mark_as_seen(file_hash, seen_path="seen_hashes.txt"):
    # "a" = append mode: adds a new line without erasing what's already there.
    with open(seen_path, "a") as f:
        f.write(file_hash + "\n")


if __name__ == "__main__":
    import sys

    path = sys.argv[1]
    file_hash = hash_file(path)

    if is_duplicate(file_hash):
        print("Already ingested, skipping.")
    else:
        print("New document, proceeding.")
        mark_as_seen(file_hash)
