import hashlib
import os


def hash_file(path):
    with open(path, "rb") as f:
        file_bytes = f.read()
    return hashlib.sha256(file_bytes).hexdigest()


def is_duplicate(file_hash, seen_path="seen_hashes.txt"):
    try:
        with open(seen_path, "r") as f:
            seen_hashes = f.read().splitlines()
    except FileNotFoundError:
        return False

    return file_hash in seen_hashes


def mark_as_seen(file_hash, seen_path="seen_hashes.txt"):
    parent_dir = os.path.dirname(seen_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    with open(seen_path, "a") as f:
        f.write(file_hash + "\n")


def remove_hash(file_hash, seen_path="seen_hashes.txt"):
    try:
        with open(seen_path, "r") as f:
            seen_hashes = f.read().splitlines()
    except FileNotFoundError:
        return

    seen_hashes = [h for h in seen_hashes if h != file_hash]
    with open(seen_path, "w") as f:
        for h in seen_hashes:
            f.write(h + "\n")


if __name__ == "__main__":
    import sys

    path = sys.argv[1]
    file_hash = hash_file(path)

    if is_duplicate(file_hash):
        print("Already ingested, skipping.")
    else:
        print("New document, proceeding.")
        mark_as_seen(file_hash)
