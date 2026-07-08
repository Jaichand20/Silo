import hashlib
import os
import re
import shutil

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from dedupe import remove_hash
from documents import documents_path, list_documents, remove_document
from store import delete_chat, delete_document, process_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
CHAT_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_chat_id(chat_id):
    if not CHAT_ID_RE.match(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat_id")


@app.post("/ingest")
def ingest(files: list[UploadFile] = File(...), chat_id: str = Form(...)):
    validate_chat_id(chat_id)

    chat_upload_dir = os.path.join(UPLOAD_DIR, chat_id)
    os.makedirs(chat_upload_dir, exist_ok=True)

    results = []
    for file in files:
        display_name = os.path.basename(file.filename)
        file_bytes = file.file.read()
        doc_hash = hashlib.sha256(file_bytes).hexdigest()

        save_path = os.path.join(chat_upload_dir, f"{doc_hash}.pdf")
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        result = process_document(save_path, chat_id, display_name)
        if result["status"] == "empty" and os.path.exists(save_path):
            os.remove(save_path)
        results.append({"filename": display_name, **result})

    return {"results": results}


@app.get("/documents")
def documents_endpoint(chat_id: str):
    validate_chat_id(chat_id)
    return list_documents(chat_id)


@app.delete("/documents")
def delete_document_endpoint(chat_id: str, doc_hash: str):
    validate_chat_id(chat_id)

    delete_document(chat_id, doc_hash)
    remove_hash(doc_hash, seen_path=f"seen_hashes/{chat_id}.txt")
    remove_document(chat_id, doc_hash)

    file_path = os.path.join(UPLOAD_DIR, chat_id, f"{doc_hash}.pdf")
    if os.path.exists(file_path):
        os.remove(file_path)

    return {"status": "removed"}


@app.delete("/chats/{chat_id}")
def delete_chat_endpoint(chat_id: str):
    validate_chat_id(chat_id)
    delete_chat(chat_id)

    chat_upload_dir = os.path.join(UPLOAD_DIR, chat_id)
    if os.path.exists(chat_upload_dir):
        shutil.rmtree(chat_upload_dir)

    seen_path = f"seen_hashes/{chat_id}.txt"
    if os.path.exists(seen_path):
        os.remove(seen_path)

    doc_path = documents_path(chat_id)
    if os.path.exists(doc_path):
        os.remove(doc_path)

    return {"status": "deleted"}
