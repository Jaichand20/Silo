const INGESTION_URL = "http://localhost:8001";
const CHAT_URL = "http://localhost:8002";

const state = {
    chats: [],
    currentChatId: null,
    history: [],
    documents: [],
    pendingDeleteChatId: null,
};

function genChatId() {
    return crypto.randomUUID().replace(/-/g, "").slice(0, 8);
}

function chatLabel(chatId) {
    const index = state.chats.indexOf(chatId);
    return `Chat ${index + 1}`;
}

async function fetchChats() {
    try {
        const res = await fetch(`${CHAT_URL}/chats`);
        if (!res.ok) return [];
        return await res.json();
    } catch {
        return [];
    }
}

async function fetchHistory(chatId) {
    try {
        const res = await fetch(`${CHAT_URL}/history?chat_id=${encodeURIComponent(chatId)}`);
        if (!res.ok) return [];
        return await res.json();
    } catch {
        return [];
    }
}

async function fetchDocuments(chatId) {
    try {
        const res = await fetch(`${INGESTION_URL}/documents?chat_id=${encodeURIComponent(chatId)}`);
        if (!res.ok) return [];
        return await res.json();
    } catch {
        return [];
    }
}

async function deleteChatBackend(chatId) {
    await Promise.allSettled([
        fetch(`${INGESTION_URL}/chats/${encodeURIComponent(chatId)}`, { method: "DELETE" }),
        fetch(`${CHAT_URL}/chats/${encodeURIComponent(chatId)}`, { method: "DELETE" }),
    ]);
}

function renderSessions() {
    const container = document.getElementById("sessions");
    container.innerHTML = "";

    state.chats.forEach((chatId, i) => {
        const row = document.createElement("div");
        row.className = "session-row" + (chatId === state.currentChatId ? " active" : "");

        const label = document.createElement("button");
        label.className = "session-label";
        label.textContent = `Chat ${i + 1}`;
        label.onclick = () => switchChat(chatId);

        const del = document.createElement("button");
        del.className = "session-delete";
        del.textContent = "×";
        del.onclick = () => requestDeleteChat(chatId);

        row.appendChild(label);
        row.appendChild(del);
        container.appendChild(row);
    });
}

function renderMessages() {
    const container = document.getElementById("messages");
    container.innerHTML = "";

    if (state.history.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h2>Ask a question about your documents</h2>
            </div>
        `;
        return;
    }

    state.history.forEach((msg) => {
        const wrap = document.createElement("div");
        wrap.className = `msg ${msg.role}`;

        const label = document.createElement("div");
        label.className = "msg-label";
        label.textContent = msg.role === "user" ? "You" : "Silo";

        const bubble = document.createElement("div");
        bubble.className = "msg-bubble";
        bubble.textContent = msg.content;

        wrap.appendChild(label);
        wrap.appendChild(bubble);
        container.appendChild(wrap);
    });

    container.scrollTop = container.scrollHeight;
}

function renderDocuments() {
    const list = document.getElementById("doc-list");
    const count = document.getElementById("doc-count");
    list.innerHTML = "";
    count.textContent = state.documents.length;

    if (state.documents.length === 0) {
        list.innerHTML = `<div class="no-docs">No documents yet.<br>Drop a PDF above.</div>`;
        return;
    }

    state.documents.forEach((doc) => {
        const row = document.createElement("div");
        row.className = "doc-row";

        row.innerHTML = `
            <div class="doc-icon">PDF</div>
            <div class="doc-meta">
                <div class="doc-name">${escapeHtml(doc.filename)}</div>
                <div class="doc-status">Uploaded</div>
            </div>
        `;

        const removeBtn = document.createElement("button");
        removeBtn.className = "doc-remove";
        removeBtn.textContent = "Remove";
        removeBtn.onclick = () => removeDocument(doc.hash);

        row.appendChild(removeBtn);
        list.appendChild(row);
    });
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function switchChat(chatId) {
    if (chatId === state.currentChatId) return;
    state.currentChatId = chatId;
    state.history = await fetchHistory(chatId);
    state.documents = await fetchDocuments(chatId);
    renderSessions();
    renderMessages();
    renderDocuments();
}

function newChat() {
    const chatId = genChatId();
    state.chats.push(chatId);
    state.currentChatId = chatId;
    state.history = [];
    state.documents = [];
    renderSessions();
    renderMessages();
    renderDocuments();
}

function requestDeleteChat(chatId) {
    if (sessionStorage.getItem("silo_skip_delete_confirm") === "true") {
        finishChatDeletion(chatId);
        return;
    }
    state.pendingDeleteChatId = chatId;
    document.getElementById("modal-title").textContent = `Delete ${chatLabel(chatId)}?`;
    document.getElementById("modal-dont-ask").checked = false;
    document.getElementById("modal-overlay").classList.remove("hidden");
}

async function finishChatDeletion(chatId) {
    await deleteChatBackend(chatId);
    state.chats = state.chats.filter((id) => id !== chatId);

    if (state.chats.length === 0) {
        const newId = genChatId();
        state.chats = [newId];
        state.currentChatId = newId;
        state.history = [];
        state.documents = [];
    } else if (state.currentChatId === chatId) {
        state.currentChatId = state.chats[state.chats.length - 1];
        state.history = await fetchHistory(state.currentChatId);
        state.documents = await fetchDocuments(state.currentChatId);
    }

    renderSessions();
    renderMessages();
    renderDocuments();
}

async function removeDocument(docHash) {
    try {
        await fetch(
            `${INGESTION_URL}/documents?chat_id=${encodeURIComponent(state.currentChatId)}&doc_hash=${encodeURIComponent(docHash)}`,
            { method: "DELETE" }
        );
        state.documents = await fetchDocuments(state.currentChatId);
        renderDocuments();
    } catch (e) {
        alert(`Could not remove document: ${e}`);
    }
}

async function uploadFiles(files) {
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (const file of files) {
        formData.append("files", file);
    }
    formData.append("chat_id", state.currentChatId);

    try {
        const res = await fetch(`${INGESTION_URL}/ingest`, {
            method: "POST",
            body: formData,
        });
        if (!res.ok) throw new Error(`status ${res.status}`);
        await res.json();
        state.documents = await fetchDocuments(state.currentChatId);
        renderDocuments();
    } catch (e) {
        alert(`Ingestion service unavailable: ${e}`);
    }
}

async function sendMessage() {
    const input = document.getElementById("chat-input");
    const query = input.value.trim();
    if (!query) return;

    input.value = "";
    input.style.height = "auto";

    state.history.push({ role: "user", content: query });
    state.history.push({ role: "assistant", content: "" });
    renderMessages();

    const assistantIndex = state.history.length - 1;
    const bubbles = document.querySelectorAll(".msg-bubble");
    const assistantBubble = bubbles[bubbles.length - 1];
    const cursor = document.createElement("span");
    cursor.className = "cursor";
    assistantBubble.appendChild(cursor);

    try {
        const res = await fetch(`${CHAT_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query, chat_id: state.currentChatId }),
        });
        if (!res.ok) throw new Error(`status ${res.status}`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let reply = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            reply += decoder.decode(value, { stream: true });
            state.history[assistantIndex].content = reply;
            assistantBubble.textContent = reply;
            assistantBubble.appendChild(cursor);
            document.getElementById("messages").scrollTop = document.getElementById("messages").scrollHeight;
        }

        cursor.remove();
    } catch (e) {
        state.history[assistantIndex].content = `Chat service unavailable: ${e}`;
        renderMessages();
    }
}

function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.getAttribute("data-theme") === "dark";
    if (isDark) {
        html.removeAttribute("data-theme");
        document.getElementById("theme-toggle").textContent = "Dark";
    } else {
        html.setAttribute("data-theme", "dark");
        document.getElementById("theme-toggle").textContent = "Light";
    }
}

function setupEventListeners() {
    document.getElementById("new-chat-btn").onclick = newChat;
    document.getElementById("theme-toggle").onclick = toggleTheme;

    const input = document.getElementById("chat-input");
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    input.addEventListener("input", () => {
        input.style.height = "auto";
        input.style.height = `${input.scrollHeight}px`;
    });
    document.getElementById("send-btn").onclick = sendMessage;

    const fileInput = document.getElementById("file-input");
    const uploadZone = document.getElementById("upload-zone");
    uploadZone.onclick = () => fileInput.click();
    fileInput.onchange = () => {
        uploadFiles(fileInput.files);
        fileInput.value = "";
    };
    uploadZone.ondragover = (e) => {
        e.preventDefault();
        uploadZone.classList.add("dragover");
    };
    uploadZone.ondragleave = () => uploadZone.classList.remove("dragover");
    uploadZone.ondrop = (e) => {
        e.preventDefault();
        uploadZone.classList.remove("dragover");
        uploadFiles(e.dataTransfer.files);
    };

    document.getElementById("modal-confirm").onclick = () => {
        if (document.getElementById("modal-dont-ask").checked) {
            sessionStorage.setItem("silo_skip_delete_confirm", "true");
        }
        document.getElementById("modal-overlay").classList.add("hidden");
        const chatId = state.pendingDeleteChatId;
        state.pendingDeleteChatId = null;
        finishChatDeletion(chatId);
    };
    document.getElementById("modal-cancel").onclick = () => {
        state.pendingDeleteChatId = null;
        document.getElementById("modal-overlay").classList.add("hidden");
    };
}

async function init() {
    setupEventListeners();

    const chats = await fetchChats();
    if (chats.length === 0) {
        const chatId = genChatId();
        state.chats = [chatId];
        state.currentChatId = chatId;
        state.history = [];
    } else {
        state.chats = chats;
        state.currentChatId = chats[chats.length - 1];
        state.history = await fetchHistory(state.currentChatId);
    }
    state.documents = await fetchDocuments(state.currentChatId);

    renderSessions();
    renderMessages();
    renderDocuments();
}

init();
