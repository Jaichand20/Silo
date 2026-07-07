from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from chat import ask
from memory import add_message, load_history, save_history

app = FastAPI()


class ChatRequest(BaseModel):
    query: str


@app.get("/history")
def history_endpoint():
    return load_history()


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    history = load_history()

    def stream_and_save():
        tokens = []
        for token in ask(request.query, history):
            tokens.append(token)
            yield token

        reply = "".join(tokens)
        add_message(history, "user", request.query)
        add_message(history, "assistant", reply)
        save_history(history)

    return StreamingResponse(stream_and_save(), media_type="text/plain")
