import json
import os

DOCUMENTS_DIR = "documents"


def documents_path(chat_id):
    return f"{DOCUMENTS_DIR}/{chat_id}.json"


def list_documents(chat_id):
    path = documents_path(chat_id)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def add_document(chat_id, doc_hash, filename):
    documents = list_documents(chat_id)
    documents.append({"hash": doc_hash, "filename": filename})

    path = documents_path(chat_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2)


def remove_document(chat_id, doc_hash):
    documents = list_documents(chat_id)
    documents = [d for d in documents if d["hash"] != doc_hash]

    path = documents_path(chat_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2)
