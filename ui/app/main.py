import os
import uuid

import requests
import streamlit as st

INGESTION_URL = os.environ.get("INGESTION_URL", "http://localhost:8001")
CHAT_URL = os.environ.get("CHAT_URL", "http://localhost:8002")

st.set_page_config(page_title="Silo", layout="wide")
st.subheader("Silo")


def fetch_history(chat_id):
    try:
        response = requests.get(f"{CHAT_URL}/history", params={"chat_id": chat_id})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []


def fetch_documents(chat_id):
    try:
        response = requests.get(f"{INGESTION_URL}/documents", params={"chat_id": chat_id})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []


def delete_chat_backend(chat_id):
    try:
        requests.delete(f"{INGESTION_URL}/chats/{chat_id}")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not fully delete chat data: {e}")
    try:
        requests.delete(f"{CHAT_URL}/chats/{chat_id}")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not fully delete chat data: {e}")


def finish_chat_deletion(chat_id):
    delete_chat_backend(chat_id)
    st.session_state.chats.remove(chat_id)

    if not st.session_state.chats:
        new_chat_id = uuid.uuid4().hex[:8]
        st.session_state.chats = [new_chat_id]
        st.session_state.current_chat_id = new_chat_id
        st.session_state.history = []
    elif st.session_state.current_chat_id == chat_id:
        st.session_state.current_chat_id = st.session_state.chats[-1]
        st.session_state.history = fetch_history(st.session_state.current_chat_id)


@st.dialog("Delete chat")
def confirm_delete_dialog(chat_id, label):
    st.write(f"Delete {label}? This removes all of its documents and history.")
    dont_ask_again = st.checkbox("Don't ask me again")

    confirm_col, cancel_col = st.columns(2)
    if confirm_col.button("Delete", type="primary", use_container_width=True):
        if dont_ask_again:
            st.session_state.skip_delete_confirm = True
        st.session_state.pending_delete_chat_id = None
        finish_chat_deletion(chat_id)
        st.rerun()
    if cancel_col.button("Cancel", use_container_width=True):
        st.session_state.pending_delete_chat_id = None
        st.rerun()


def stream_chat(query, chat_id):
    response = requests.post(
        f"{CHAT_URL}/chat",
        json={"query": query, "chat_id": chat_id},
        stream=True,
    )
    response.raise_for_status()
    response.encoding = "utf-8"
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        yield chunk


if "skip_delete_confirm" not in st.session_state:
    st.session_state.skip_delete_confirm = False

if "pending_delete_chat_id" not in st.session_state:
    st.session_state.pending_delete_chat_id = None

if "chats" not in st.session_state:
    try:
        response = requests.get(f"{CHAT_URL}/chats")
        response.raise_for_status()
        chats = response.json()
    except requests.exceptions.RequestException:
        chats = []

    if not chats:
        chat_id = uuid.uuid4().hex[:8]
        st.session_state.chats = [chat_id]
        st.session_state.current_chat_id = chat_id
        st.session_state.history = []
    else:
        st.session_state.chats = chats
        st.session_state.current_chat_id = chats[-1]
        st.session_state.history = fetch_history(chats[-1])

if st.sidebar.button("+ New Chat"):
    chat_id = uuid.uuid4().hex[:8]
    st.session_state.chats.append(chat_id)
    st.session_state.current_chat_id = chat_id
    st.session_state.history = []
    st.rerun()

st.sidebar.write("Chats")
for i, chat_id in enumerate(st.session_state.chats):
    is_current = chat_id == st.session_state.current_chat_id
    tab_col, delete_col = st.sidebar.columns([4, 1])
    clicked = tab_col.button(
        f"Chat {i + 1}",
        key=f"chat_tab_{chat_id}",
        type="primary" if is_current else "secondary",
        use_container_width=True,
    )
    delete_clicked = delete_col.button("×", key=f"delete_chat_{chat_id}")

    if clicked and not is_current:
        st.session_state.current_chat_id = chat_id
        st.session_state.history = fetch_history(chat_id)
        st.rerun()

    if delete_clicked:
        if st.session_state.skip_delete_confirm:
            finish_chat_deletion(chat_id)
        else:
            st.session_state.pending_delete_chat_id = chat_id
        st.rerun()

if st.session_state.pending_delete_chat_id is not None:
    pending_id = st.session_state.pending_delete_chat_id
    pending_label = f"Chat {st.session_state.chats.index(pending_id) + 1}"
    confirm_delete_dialog(pending_id, pending_label)

col_chat, col_sources = st.columns([2, 1])

with col_sources:
    st.subheader("Sources")

    with st.form("upload_form", clear_on_submit=True):
        uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
        submitted = st.form_submit_button("Upload")

    if submitted and uploaded_files:
        try:
            files = [
                ("files", (f.name, f.getvalue(), "application/pdf")) for f in uploaded_files
            ]
            data = {"chat_id": st.session_state.current_chat_id}
            response = requests.post(f"{INGESTION_URL}/ingest", files=files, data=data)
            response.raise_for_status()
            for result in response.json()["results"]:
                if result["status"] == "duplicate":
                    st.info(f"{result['filename']} was already ingested.")
                else:
                    st.success(f"Stored {result['chunks_stored']} chunks from {result['filename']}.")
        except requests.exceptions.RequestException as e:
            st.error(f"Ingestion service unavailable: {e}")

    documents = fetch_documents(st.session_state.current_chat_id)
    if not documents:
        st.caption("No documents uploaded yet.")
    for doc in documents:
        doc_name_col, doc_remove_col = st.columns([4, 1])
        doc_name_col.write(doc["filename"])
        if doc_remove_col.button("Remove", key=f"remove_{doc['hash']}"):
            try:
                response = requests.delete(
                    f"{INGESTION_URL}/documents",
                    params={"chat_id": st.session_state.current_chat_id, "doc_hash": doc["hash"]},
                )
                response.raise_for_status()
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Could not remove document: {e}")

with col_chat:
    for message in st.session_state.history:
        st.chat_message(message["role"]).write(message["content"])

    query = st.chat_input("Ask a question about your documents...")
    if query:
        st.session_state.history.append({"role": "user", "content": query})
        st.chat_message("user").write(query)

        with st.chat_message("assistant"):
            try:
                reply = st.write_stream(stream_chat(query, st.session_state.current_chat_id))
            except requests.exceptions.RequestException as e:
                reply = None
                st.error(f"Chat service unavailable: {e}")

        if reply is not None:
            st.session_state.history.append({"role": "assistant", "content": reply})
