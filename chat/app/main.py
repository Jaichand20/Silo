import glob
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from chat import ask
from memory import HISTORY_DIR, add_message, history_path, load_history, save_history

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    chat_id: str


@app.get("/chats")
def chats_endpoint():
    paths = glob.glob(os.path.join(HISTORY_DIR, "*.json"))
    paths.sort(key=os.path.getmtime)
    return [os.path.splitext(os.path.basename(path))[0] for path in paths]


@app.get("/history")
def history_endpoint(chat_id: str):
    return load_history(path=history_path(chat_id))


@app.delete("/chats/{chat_id}")
def delete_chat_endpoint(chat_id: str):
    path = history_path(chat_id)
    if os.path.exists(path):
        os.remove(path)
    return {"status": "deleted"}


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    history = load_history(path=history_path(request.chat_id))

    def stream_and_save():
        tokens = []
        for token in ask(request.query, history, request.chat_id):
            tokens.append(token)
            yield token

        reply = "".join(tokens)
        add_message(history, "user", request.query)
        add_message(history, "assistant", reply)
        save_history(history, path=history_path(request.chat_id))

    return StreamingResponse(stream_and_save(), media_type="text/plain")
