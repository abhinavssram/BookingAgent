const connectContainer = document.getElementById("connectContainer");
const chatWrapper = document.getElementById("chatWrapper");
const chatInputContainer = document.getElementById("chatInputContainer");
const chatHistory = document.getElementById("chatHistory");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const introTextEl = document.getElementById("introText");
const introMessage = "Hello, I'm your booking assistant!";

let conversationId = null;
let typingBubble = null;
let activeConfirmationRow = null;

chatInput.addEventListener("input", () => {
  sendBtn.disabled = chatInput.value.trim().length === 0;
});

let introIndex = 0;

function typeIntro() {
  if (!introTextEl) return;

  if (introIndex < introMessage.length) {
    introTextEl.textContent += introMessage[introIndex];
    introIndex++;
    setTimeout(typeIntro, 35);
  }
}

typeIntro();

fetch("/me")
  .then((res) => {
    if (!res.ok) throw new Error();
    return res.json();
  })
  .then(showChat)
  .catch(showConnect);

function showChat() {
  connectContainer.classList.add("hidden");
  chatWrapper.classList.remove("hidden");
}

function showConnect() {
  connectContainer.classList.remove("hidden");
  chatWrapper.classList.add("hidden");
}

function connectCalendar() {
  window.location.href = "/connect-calendar";
}

function handleKey(e) {
  if (e.key === "Enter") sendMessage();
}

function getTalkPayload(extra = {}) {
  return {
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    client_time: new Date().toISOString(),
    conversation_id: conversationId,
    ...extra,
  };
}

function setInputEnabled(enabled) {
  chatInput.disabled = !enabled;
  sendBtn.disabled = !enabled || chatInput.value.trim().length === 0;
  if (enabled) {
    chatInput.focus();
  }
}

function postTalk(body) {
  return fetch("/talk", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((res) => {
    if (!res.ok) {
      return res.json().then((err) => {
        throw new Error(err.detail || "Request failed");
      });
    }
    return res.json();
  });
}

function handleTalkResponse(data) {
  removeTyping();

  if (data.conversation_id) {
    conversationId = data.conversation_id;
  }

  if (data.interrupt) {
    showConfirmationPrompt(data.interrupt);
    return;
  }

  if (data.status === "awaiting_confirmation") {
    appendMessage("Please confirm the booking to continue.", "ai");
    setInputEnabled(false);
    return;
  }

  clearActiveConfirmation();
  setInputEnabled(true);

  const last = data.messages?.at(-1);
  if (last?.content) {
    appendMessage(last.content, "ai", true);
  }
}

function handleTalkError(error) {
  removeTyping();
  clearActiveConfirmation();
  setInputEnabled(true);
  appendMessage(error?.message || "Something went wrong.", "ai");
}

function sendMessage() {
  if (sendBtn.disabled || activeConfirmationRow) return;

  const text = chatInput.value.trim();
  if (!text) return;

  appendMessage(text, "user");
  chatInput.value = "";
  setInputEnabled(false);
  showTyping();

  postTalk(getTalkPayload({ query: text }))
    .then(handleTalkResponse)
    .catch(handleTalkError);
}

function resumeBooking(approved) {
  if (!activeConfirmationRow) return;

  const actionLabel = approved ? "Confirmed" : "Cancelled";
  appendMessage(actionLabel, "user");

  disableConfirmationButtons();
  setInputEnabled(false);
  showTyping();

  postTalk(getTalkPayload({ resume: { approved } }))
    .then(handleTalkResponse)
    .catch(handleTalkError);
}

function formatDateTime(value) {
  if (!value) return null;

  const raw = typeof value === "string" ? value : value.dateTime;
  if (!raw) return null;

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;

  return date.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function buildConfirmationCopy(interrupt) {
  if (interrupt.message) {
    return interrupt.message;
  }

  const start = formatDateTime(interrupt.start);
  const end = formatDateTime(interrupt.end);
  const title = interrupt.summary || "Appointment";

  if (start && end) {
    return `Please confirm: "${title}" from ${start} to ${end}.`;
  }

  return "Please confirm this booking before it is created on your calendar.";
}

function showConfirmationPrompt(interrupt) {
  clearActiveConfirmation();
  setInputEnabled(false);

  const row = document.createElement("div");
  row.className = "message-row ai confirmation-row";

  const bubble = document.createElement("div");
  bubble.className = "message ai confirmation-card";

  const copy = document.createElement("p");
  copy.className = "confirmation-copy";
  copy.textContent = buildConfirmationCopy(interrupt);
  bubble.appendChild(copy);

  const details = document.createElement("div");
  details.className = "confirmation-details";

  if (interrupt.summary) {
    details.appendChild(createDetailRow("Title", interrupt.summary));
  }

  const startLabel = formatDateTime(interrupt.start);
  const endLabel = formatDateTime(interrupt.end);
  if (startLabel) {
    details.appendChild(createDetailRow("Starts", startLabel));
  }
  if (endLabel) {
    details.appendChild(createDetailRow("Ends", endLabel));
  }
  if (interrupt.description) {
    details.appendChild(createDetailRow("Notes", interrupt.description));
  }

  if (details.childElementCount > 0) {
    bubble.appendChild(details);
  }

  const actions = document.createElement("div");
  actions.className = "confirmation-actions";

  const confirmBtn = document.createElement("button");
  confirmBtn.type = "button";
  confirmBtn.className = "confirmation-btn confirm";
  confirmBtn.textContent = "Confirm booking";
  confirmBtn.addEventListener("click", () => resumeBooking(true));

  const cancelBtn = document.createElement("button");
  cancelBtn.type = "button";
  cancelBtn.className = "confirmation-btn cancel";
  cancelBtn.textContent = "Cancel";
  cancelBtn.addEventListener("click", () => resumeBooking(false));

  actions.appendChild(confirmBtn);
  actions.appendChild(cancelBtn);
  bubble.appendChild(actions);

  row.appendChild(bubble);
  chatHistory.appendChild(row);
  chatHistory.scrollTop = chatHistory.scrollHeight;

  activeConfirmationRow = row;
}

function createDetailRow(label, value) {
  const item = document.createElement("div");
  item.className = "confirmation-detail";

  const labelEl = document.createElement("span");
  labelEl.className = "confirmation-detail-label";
  labelEl.textContent = label;

  const valueEl = document.createElement("span");
  valueEl.className = "confirmation-detail-value";
  valueEl.textContent = value;

  item.appendChild(labelEl);
  item.appendChild(valueEl);
  return item;
}

function disableConfirmationButtons() {
  if (!activeConfirmationRow) return;

  activeConfirmationRow
    .querySelectorAll(".confirmation-btn")
    .forEach((btn) => {
      btn.disabled = true;
    });

  activeConfirmationRow.classList.add("resolved");
}

function clearActiveConfirmation() {
  if (activeConfirmationRow) {
    activeConfirmationRow.remove();
    activeConfirmationRow = null;
  }
}

/* ---------- Messages ---------- */
function appendMessage(text, type, markdown = false) {
  const row = document.createElement("div");
  row.className = `message-row ${type}`;

  const bubble = document.createElement("div");
  bubble.className = `message ${type}`;

  if (markdown) {
    bubble.innerHTML = renderMarkdown(text);
  } else {
    bubble.textContent = text;
  }

  row.appendChild(bubble);
  chatHistory.appendChild(row);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function showTyping() {
  typingBubble = document.createElement("div");
  typingBubble.className = "message ai typing";

  typingBubble.innerHTML = `
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  `;

  chatHistory.appendChild(typingBubble);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function removeTyping() {
  if (typingBubble) {
    typingBubble.remove();
    typingBubble = null;
  }
}

function renderMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/^- (.*)$/gm, "• $1")
    .replace(/\n/g, "<br>");
}
