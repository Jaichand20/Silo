import os
import shutil

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from dedupe import remove_hash
from documents import documents_path, list_documents, remove_document
from store import delete_chat, delete_document, process_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"


@app.post("/ingest")
async def ingest(files: list[UploadFile] = File(...), chat_id: str = Form(...)):
    chat_upload_dir = os.path.join(UPLOAD_DIR, chat_id)
    os.makedirs(chat_upload_dir, exist_ok=True)

    results = []
    for file in files:
        save_path = os.path.join(chat_upload_dir, file.filename)
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = process_document(save_path, chat_id)
        results.append({"filename": file.filename, **result})

    return {"results": results}


@app.get("/documents")
def documents_endpoint(chat_id: str):
    return list_documents(chat_id)


@app.delete("/documents")
def delete_document_endpoint(chat_id: str, doc_hash: str):
    documents = list_documents(chat_id)
    match = next((d for d in documents if d["hash"] == doc_hash), None)

    delete_document(chat_id, doc_hash)
    remove_hash(doc_hash, seen_path=f"seen_hashes/{chat_id}.txt")
    remove_document(chat_id, doc_hash)

    if match is not None:
        file_path = os.path.join(UPLOAD_DIR, chat_id, match["filename"])
        if os.path.exists(file_path):
            os.remove(file_path)

    return {"status": "removed"}


@app.delete("/chats/{chat_id}")
def delete_chat_endpoint(chat_id: str):
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
