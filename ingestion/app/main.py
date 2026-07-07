import os
import shutil

from fastapi import FastAPI, UploadFile

from store import process_document

app = FastAPI()

# Where uploaded PDFs get saved before processing. Gitignored (see
# .gitignore's "uploads/" rule) since it holds user data, not source code.
UPLOAD_DIR = "uploads"


@app.post("/ingest")
async def ingest(file: UploadFile):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(UPLOAD_DIR, file.filename)

    # Copy the uploaded file straight to disk in chunks rather than
    # reading it all into memory first — process_document() needs a real
    # file path anyway (pypdf reads from disk), not raw bytes.
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = process_document(save_path)
    return {"filename": file.filename, **result}
