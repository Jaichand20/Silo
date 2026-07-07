import json
import os

import requests

from memory import add_message, load_history, recent_messages, save_history
from prompt import build_system_prompt
from retrieve import retrieve_top_chunks

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = "gemma4"


def ask(query, history, chat_id):
    chunks = retrieve_top_chunks(query, chat_id)
    system_prompt = build_system_prompt(chunks)

    messages = [{"role": "system", "content": system_prompt}]
    messages += recent_messages(history)
    messages.append({"role": "user", "content": query})

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={"model": MODEL, "messages": messages, "stream": True},
        stream=True,
    )
    response.raise_for_status()

    for line in response.iter_lines():
        if not line:
            continue
        piece = json.loads(line)
        yield piece["message"]["content"]
        if piece.get("done"):
            break


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    chat_id = sys.argv[1]
    history = load_history()

    print("Silo chat. Type 'exit' to quit.")
    while True:
        query = input("\nYou: ")
        if query.strip().lower() == "exit":
            break

        print("Assistant: ", end="")
        tokens = []
        for token in ask(query, history, chat_id):
            print(token, end="", flush=True)
            tokens.append(token)
        print()
        reply = "".join(tokens)

        add_message(history, "user", query)
        add_message(history, "assistant", reply)
        save_history(history)
