import json
import os

# Where the full conversation gets saved between runs. This is a plain
# JSON file for now (simplest thing that works) — a real multi-user app
# would need a database per conversation, but this project is single-user
# and local, so one file is enough.
HISTORY_PATH = "chat_history.json"

# How many past MESSAGES (not full back-and-forth turns) get sent back to
# the model on every request. Each user question and each assistant reply
# both count as one message, so 6 means "last 3 question/answer pairs."
# This is what stops the prompt sent to Gemma 4 from growing forever as a
# conversation gets longer — old messages are still saved to disk, just
# not replayed.
MAX_MESSAGES = 6


def load_history(path=HISTORY_PATH):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history, path=HISTORY_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def add_message(history, role, content):
    # role is "user" or "assistant" — this matches the format Ollama's
    # /api/chat endpoint expects for each message.
    history.append({"role": role, "content": content})


def recent_messages(history, max_messages=MAX_MESSAGES):
    # A plain list slice: the last `max_messages` entries. If history is
    # shorter than that, Python slicing just returns the whole list — no
    # special-casing needed.
    return history[-max_messages:]


if __name__ == "__main__":
    # Quick manual check of the trim behaviour.
    history = []
    for i in range(10):
        add_message(history, "user" if i % 2 == 0 else "assistant", f"message {i}")

    print(f"Full history has {len(history)} messages.")
    print(f"Replayed to model: {recent_messages(history)}")
