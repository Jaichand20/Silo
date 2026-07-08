import json
import os

HISTORY_DIR = "chat_histories"

MAX_MESSAGES = 6


def history_path(chat_id):
    return f"{HISTORY_DIR}/{chat_id}.json"


def load_history(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history, path):
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def add_message(history, role, content):
    history.append({"role": role, "content": content})


def recent_messages(history, max_messages=MAX_MESSAGES):
    return history[-max_messages:]


if __name__ == "__main__":
    history = []
    for i in range(10):
        add_message(history, "user" if i % 2 == 0 else "assistant", f"message {i}")

    print(f"Full history has {len(history)} messages.")
    print(f"Replayed to model: {recent_messages(history)}")
