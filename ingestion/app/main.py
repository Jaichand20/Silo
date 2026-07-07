import os
import shutil

from fastapi import FastAPI, UploadFile

from store import process_document

app = FastAPI()

UPLOAD_DIR = "uploads"


@app.post("/ingest")
async def ingest(file: UploadFile):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = process_document(save_path)
    return {"filename": file.filename, **result}
