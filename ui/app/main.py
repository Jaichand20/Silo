import os

import requests
import streamlit as st

INGESTION_URL = os.environ.get("INGESTION_URL", "http://localhost:8001")
CHAT_URL = os.environ.get("CHAT_URL", "http://localhost:8002")

st.set_page_config(page_title="Silo")
st.title("Silo")

if "history" not in st.session_state:
    try:
        response = requests.get(f"{CHAT_URL}/history")
        response.raise_for_status()
        st.session_state.history = response.json()
    except requests.exceptions.RequestException:
        st.session_state.history = []

with st.form("upload_form", clear_on_submit=True):
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    submitted = st.form_submit_button("Upload")

if submitted and uploaded_file is not None:
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        response = requests.post(f"{INGESTION_URL}/ingest", files=files)
        response.raise_for_status()
        result = response.json()
        if result["status"] == "duplicate":
            st.info(f"{result['filename']} was already ingested.")
        else:
            st.success(f"Stored {result['chunks_stored']} chunks from {result['filename']}.")
    except requests.exceptions.RequestException as e:
        st.error(f"Ingestion service unavailable: {e}")

for message in st.session_state.history:
    st.chat_message(message["role"]).write(message["content"])


def stream_chat(query):
    response = requests.post(f"{CHAT_URL}/chat", json={"query": query}, stream=True)
    response.raise_for_status()
    response.encoding = "utf-8"
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        yield chunk


query = st.chat_input("Ask a question about your documents...")
if query:
    st.session_state.history.append({"role": "user", "content": query})
    st.chat_message("user").write(query)

    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(stream_chat(query))
        except requests.exceptions.RequestException as e:
            reply = None
            st.error(f"Chat service unavailable: {e}")

    if reply is not None:
        st.session_state.history.append({"role": "assistant", "content": reply})
