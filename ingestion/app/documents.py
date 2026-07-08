import json
import os
import threading

DOCUMENTS_DIR = "documents"

_lock = threading.Lock()


def documents_path(chat_id):
    return f"{DOCUMENTS_DIR}/{chat_id}.json"


def list_documents(chat_id):
    path = documents_path(chat_id)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_documents(path, documents):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2)
    os.replace(tmp_path, path)


def add_document(chat_id, doc_hash, filename):
    with _lock:
        documents = list_documents(chat_id)
        documents.append({"hash": doc_hash, "filename": filename})
        _write_documents(documents_path(chat_id), documents)


def remove_document(chat_id, doc_hash):
    with _lock:
        documents = list_documents(chat_id)
        documents = [d for d in documents if d["hash"] != doc_hash]
        _write_documents(documents_path(chat_id), documents)
