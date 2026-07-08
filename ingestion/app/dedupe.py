import hashlib
import os
import threading

_lock = threading.Lock()


def hash_file(path):
    with open(path, "rb") as f:
        file_bytes = f.read()
    return hashlib.sha256(file_bytes).hexdigest()


def is_duplicate(file_hash, seen_path):
    try:
        with open(seen_path, "r") as f:
            seen_hashes = f.read().splitlines()
    except FileNotFoundError:
        return False

    return file_hash in seen_hashes


def mark_as_seen(file_hash, seen_path):
    with _lock:
        parent_dir = os.path.dirname(seen_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(seen_path, "a") as f:
            f.write(file_hash + "\n")


def remove_hash(file_hash, seen_path):
    with _lock:
        try:
            with open(seen_path, "r") as f:
                seen_hashes = f.read().splitlines()
        except FileNotFoundError:
            return

        seen_hashes = [h for h in seen_hashes if h != file_hash]
        with open(seen_path, "w") as f:
            for h in seen_hashes:
                f.write(h + "\n")
