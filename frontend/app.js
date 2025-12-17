const connectContainer = document.getElementById("connectContainer");
const chatWrapper = document.getElementById("chatWrapper");
const chatInputContainer = document.getElementById("chatInputContainer");
const chatHistory = document.getElementById("chatHistory");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");

let conversationId = null;
let typingBubble = null;

chatInput.addEventListener("input", () => {
  sendBtn.disabled = input.value.trim().length === 0;
});

fetch("/me")
  .then(res => {
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

function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;

  appendMessage(text, "user");
  chatInput.value = "";
  chatInput.disabled = true;

  showTyping();

  fetch("/talk", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: text,
      timezone: "Asia/Kolkata",
      conversation_id: conversationId
    })
  })
    .then(res => res.json())
    .then(data => {
      removeTyping();
      chatInput.disabled = false;
      sendBtn.disabled = chatInput.value.trim().length === 0;
      chatInput.focus();

      if (data.conversation_id) {
        conversationId = data.conversation_id;
      }

      const last = data.messages?.at(-1);
      if (last?.content) {
        appendMessage(last.content, "ai", true);
      }
    })
    .catch(() => {
      removeTyping();
      chatInput.disabled = false;
      appendMessage("Something went wrong.", "ai");
    });
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
