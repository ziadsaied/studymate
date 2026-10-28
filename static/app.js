// Cache DOM elements once; every UI update below uses these shared references.
const threadListEl = document.getElementById("thread-list");
const messagesEl = document.getElementById("messages");
const emptyStateEl = document.getElementById("empty-state");
const chatTitleEl = document.getElementById("chat-title");
const chatFormEl = document.getElementById("chat-form");
const chatInputEl = document.getElementById("chat-input");
const sendBtnEl = document.getElementById("send-btn");
const newChatBtnEl = document.getElementById("new-chat");
const pdfInputEl = document.getElementById("pdf-input");
const uploadStatusEl = document.getElementById("upload-status");
const userSelectEl = document.getElementById("user-select");
const addUserFormEl = document.getElementById("add-user-form");
const newUserNameEl = document.getElementById("new-user-name");
const userStatusEl = document.getElementById("user-status");
const promptCards = document.querySelectorAll("[data-prompt]");

// A null ID means the user is composing the first message of a new conversation.
let currentThreadId = null;
let threads = [];
let currentUser = null;
let users = [];

function newThreadId() {
  // Browser-generated UUIDs keep LangGraph checkpoints separate between chats.
  return crypto.randomUUID();
}

function clearMessages() {
  messagesEl.innerHTML = "";
}

function showEmptyState() {
  clearMessages();
  messagesEl.appendChild(emptyStateEl);
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function appendMessage(role, text, sources) {
  // textContent intentionally renders model output as plain text rather than HTML.
  if (emptyStateEl.isConnected) {
    emptyStateEl.remove();
  }

  const bubble = document.createElement("div");
  bubble.className = `message ${role}`;

  const p = document.createElement("p");
  p.textContent = text;
  bubble.appendChild(p);

  if (sources && sources.length) {
    const sourcesEl = document.createElement("div");
    sourcesEl.className = "sources";
    sources.forEach((source) => {
      const chip = document.createElement("span");
      chip.className = "source-chip";
      chip.textContent = source;
      sourcesEl.appendChild(chip);
    });
    bubble.appendChild(sourcesEl);
  }

  messagesEl.appendChild(bubble);
  scrollToBottom();
  return bubble;
}

function showThinking() {
  const el = document.createElement("div");
  el.className = "thinking";
  el.id = "thinking-indicator";
  el.innerHTML =
    '<span>StudyMate is thinking</span>' +
    '<span class="thinking-dots"><span></span><span></span><span></span></span>';
  messagesEl.appendChild(el);
  scrollToBottom();
}

function hideThinking() {
  const el = document.getElementById("thinking-indicator");
  if (el) el.remove();
}

function renderThreadList() {
  // Re-rendering keeps the selected conversation and newly created threads in sync.
  threadListEl.innerHTML = "";

  if (!threads.length) {
    const empty = document.createElement("p");
    empty.className = "thread-list-empty";
    empty.textContent = "Your conversations will show up here.";
    threadListEl.appendChild(empty);
    return;
  }

  threads.forEach((thread) => {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "thread-item" + (thread.thread_id === currentThreadId ? " active" : "");
    item.textContent = thread.title || "Untitled conversation";
    item.addEventListener("click", () => selectThread(thread));
    threadListEl.appendChild(item);
  });
}

async function loadThreads() {
  // Sidebar failures should not prevent the student from continuing to chat.
  if (!currentUser) return;
  try {
    const response = await fetch(`/api/threads?user_id=${encodeURIComponent(currentUser.id)}`);
    if (!response.ok) throw new Error("Could not load conversations");
    threads = await response.json();
  } catch (err) {
    threads = [];
  }
  renderThreadList();
}

async function selectThread(thread) {
  // Loading history does not contact the model; it reads an existing checkpoint.
  currentThreadId = thread.thread_id;
  chatTitleEl.textContent = thread.title || "Untitled conversation";
  renderThreadList();
  clearMessages();

  try {
    const response = await fetch(
      `/api/threads/${thread.thread_id}/messages?user_id=${encodeURIComponent(currentUser.id)}`
    );
    if (!response.ok) throw new Error("Could not load conversation");
    const history = await response.json();
    if (!history.length) {
      showEmptyState();
      return;
    }
    history.forEach((m) => appendMessage(m.role, m.content));
  } catch (err) {
    appendMessage("system", "Couldn't load this conversation. Try again in a moment.");
  }
}

function startNewChat() {
  // The UUID is delayed until the first submitted message so empty chats are not stored.
  currentThreadId = null;
  chatTitleEl.textContent = "New conversation";
  showEmptyState();
  renderThreadList();
  chatInputEl.focus();
}

function autoResize() {
  // Reset before measuring so the textarea can shrink after text is deleted.
  chatInputEl.style.height = "auto";
  chatInputEl.style.height = `${chatInputEl.scrollHeight}px`;
}

promptCards.forEach((card) => {
  card.addEventListener("click", () => {
    chatInputEl.value = card.dataset.prompt;
    autoResize();
    chatInputEl.focus();
  });
});

async function sendMessage(text) {
  if (!currentUser) {
    appendMessage("system", "Choose or add a user before starting a chat.");
    return;
  }
  // The first message creates the stable thread ID used by the API and graph.
  const isFirstMessage = !currentThreadId;
  if (isFirstMessage) {
    currentThreadId = newThreadId();
  }

  appendMessage("user", text);
  showThinking();
  sendBtnEl.disabled = true;

  try {
    // The backend owns all model, tool, and memory work; the browser only sends text.
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, thread_id: currentThreadId, user_id: currentUser.id }),
    });

    hideThinking();

    if (!response.ok) {
      appendMessage("system", "Couldn't reach StudyMate — check the server is running and try again.");
      return;
    }

    const data = await response.json();
    appendMessage("assistant", data.answer, data.sources_used);

    if (isFirstMessage) {
      chatTitleEl.textContent = text.slice(0, 60);
    }
    await loadThreads();
  } catch (err) {
    hideThinking();
    appendMessage("system", "Couldn't reach StudyMate — check the server is running and try again.");
  } finally {
    sendBtnEl.disabled = false;
  }
}

chatFormEl.addEventListener("submit", (event) => {
  // Form submission supports both the Send button and Enter-key submission.
  event.preventDefault();
  const text = chatInputEl.value.trim();
  if (!text) return;
  chatInputEl.value = "";
  autoResize();
  sendMessage(text);
});

chatInputEl.addEventListener("input", autoResize);

chatInputEl.addEventListener("keydown", (event) => {
  // Enter sends; Shift+Enter preserves the normal multiline-textarea behavior.
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatFormEl.requestSubmit();
  }
});

newChatBtnEl.addEventListener("click", startNewChat);

function renderUserList() {
  userSelectEl.innerHTML = "";
  users.forEach((user) => {
    const option = document.createElement("option");
    option.value = user.id;
    option.textContent = user.username;
    option.selected = currentUser && user.id === currentUser.id;
    userSelectEl.appendChild(option);
  });
}

async function loadUsers(preferredUserId) {
  const response = await fetch("/api/users");
  if (!response.ok) throw new Error("Could not load users");
  users = await response.json();
  const savedUserId = preferredUserId || localStorage.getItem("studymate-active-user");
  currentUser = users.find((user) => user.id === savedUserId) || users[0] || null;
  renderUserList();
}

async function switchUser(userId) {
  const nextUser = users.find((user) => user.id === userId);
  if (!nextUser || (currentUser && nextUser.id === currentUser.id)) return;
  currentUser = nextUser;
  localStorage.setItem("studymate-active-user", currentUser.id);
  currentThreadId = null;
  threads = [];
  chatTitleEl.textContent = "New conversation";
  showEmptyState();
  renderUserList();
  renderThreadList();
  await loadThreads();
}

userSelectEl.addEventListener("change", () => switchUser(userSelectEl.value));

addUserFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = newUserNameEl.value.trim();
  if (!username) return;
  userStatusEl.textContent = "Adding user...";
  try {
    const response = await fetch("/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not add user.");
    await loadUsers(data.id);
    localStorage.setItem("studymate-active-user", data.id);
    currentThreadId = null;
    threads = [];
    chatTitleEl.textContent = "New conversation";
    showEmptyState();
    renderThreadList();
    await loadThreads();
    newUserNameEl.value = "";
    userStatusEl.textContent = `Now chatting as ${data.username}.`;
  } catch (err) {
    userStatusEl.textContent = err.message || "Could not add user.";
  }
});

pdfInputEl.addEventListener("change", async () => {
  // PDF uploads are independent of the current chat and extend the shared local index.
  const file = pdfInputEl.files[0];
  if (!file) return;

  uploadStatusEl.textContent = `Indexing ${file.name}...`;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/upload", { method: "POST", body: formData });
    if (!response.ok) {
      const err = await response.json();
      uploadStatusEl.textContent = err.detail || "Upload failed.";
      return;
    }
    uploadStatusEl.textContent = `${file.name} added to your knowledge base.`;
  } catch (err) {
    uploadStatusEl.textContent = "Upload failed — check the server is running.";
  } finally {
    pdfInputEl.value = "";
  }
});

// Start with Ziad for existing single-user installations, then remember the last profile used.
async function initializeApp() {
  try {
    const response = await fetch("/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "Ziad" }),
    });
    if (!response.ok) throw new Error("Could not initialize a user profile.");
    const ziad = await response.json();
    await loadUsers();
    if (!currentUser) currentUser = ziad;
    renderUserList();
    await loadThreads();
  } catch (err) {
    userStatusEl.textContent = "Could not load user profiles. Check the server and refresh.";
  }
}

initializeApp();
