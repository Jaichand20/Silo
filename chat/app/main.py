from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from chat import ask
from memory import add_message, load_history, save_history

app = FastAPI()


# FastAPI uses this to validate the request body: a POST to /chat must
# send JSON like {"query": "..."} or the request is rejected automatically.
class ChatRequest(BaseModel):
    query: str


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    history = load_history()

    def stream_and_save():
        # ask() is a generator (see chat/app/chat.py) — this loop pulls
        # one token at a time and immediately yields it onward, so the
        # HTTP client receives tokens as they're generated, same as the
        # CLI version prints them as they arrive.
        tokens = []
        for token in ask(request.query, history):
            tokens.append(token)
            yield token

        # This only runs once the generator above is exhausted — i.e.
        # after the full reply has been streamed to the client. Only then
        # do we record the turn and save it to disk.
        reply = "".join(tokens)
        add_message(history, "user", request.query)
        add_message(history, "assistant", reply)
        save_history(history)

    return StreamingResponse(stream_and_save(), media_type="text/plain")
