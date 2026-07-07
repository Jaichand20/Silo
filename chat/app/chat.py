import json
import os

import requests

from memory import add_message, load_history, recent_messages, save_history
from prompt import build_system_prompt
from retrieve import retrieve_top_chunks

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = "gemma4"


def ask(query, history):
    # history here is the conversation SO FAR, not yet including this new
    # question — the caller adds both the question and the reply after
    # this function returns (see the __main__ loop below).
    chunks = retrieve_top_chunks(query)
    system_prompt = build_system_prompt(chunks)

    # The system prompt is rebuilt fresh every call, since it depends on
    # THIS question's retrieved chunks. Then we add a trimmed slice of
    # past messages (memory.py's sliding window), then the new question.
    messages = [{"role": "system", "content": system_prompt}]
    messages += recent_messages(history)
    messages.append({"role": "user", "content": query})

    # stream=True on both the requests call and the Ollama payload means
    # the response arrives as many small JSON objects (one per token)
    # instead of one big blob we'd have to wait for.
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={"model": MODEL, "messages": messages, "stream": True},
        stream=True,
    )
    response.raise_for_status()

    full_reply = ""
    for line in response.iter_lines():
        if not line:
            continue
        piece = json.loads(line)
        token = piece["message"]["content"]
        print(token, end="", flush=True)
        full_reply += token
        if piece.get("done"):
            break
    print()

    return full_reply


if __name__ == "__main__":
    import sys

    # Same Windows console fix as retrieve.py — without this, printing a
    # streamed reply containing e.g. a bullet or smart quote can crash.
    sys.stdout.reconfigure(encoding="utf-8")

    history = load_history()

    print("Silo chat. Type 'exit' to quit.")
    while True:
        query = input("\nYou: ")
        if query.strip().lower() == "exit":
            break

        print("Assistant: ", end="")
        reply = ask(query, history)

        # Only now — after the reply is complete — do we record this turn
        # in the permanent history and save it to disk.
        add_message(history, "user", query)
        add_message(history, "assistant", reply)
        save_history(history)
