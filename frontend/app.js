const connectContainer = document.getElementById("connectContainer");
const chatWrapper = document.getElementById("chatWrapper");
const chatInputContainer = document.getElementById("chatInputContainer");
const chatHistory = document.getElementById("chatHistory");
const loader = document.getElementById("loader");

let conversationId = null;

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
    chatInputContainer.classList.remove("hidden");
  }
  
  function showConnect() {
    connectContainer.classList.remove("hidden");
    chatWrapper.classList.add("hidden");
    chatInputContainer.classList.add("hidden");
    loader.classList.add("hidden");
  }
  

function connectCalendar() {
  window.location.href = "/connect-calendar";
}

function handleKey(e) {
  if (e.key === "Enter") sendMessage();
}

function sendMessage() {
  const input = document.getElementById("chatInput");
  const text = input.value.trim();
  if (!text) return;

  appendMessage(text, "user");
  input.value = "";

  chatInputContainer.classList.add("hidden");
  loader.classList.remove("hidden");

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
      loader.classList.add("hidden");
      chatInputContainer.classList.remove("hidden");

      if (data.conversation_id) {
        conversationId = data.conversation_id;
      }

      const last = data.messages?.at(-1);
      if (last?.content) appendMessage(last.content, "ai");
    })
    .catch(() => {
      loader.classList.add("hidden");
      chatInputContainer.classList.remove("hidden");
      appendMessage("Error occurred.", "ai");
    });
}

function appendMessage(text, type) {
  const div = document.createElement("div");
  div.className = `message ${type}`;
  div.textContent = text;
  chatHistory.appendChild(div);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}
