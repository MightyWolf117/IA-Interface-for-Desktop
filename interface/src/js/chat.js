// ==========================================================================
// CYBER-IA // CHAT LLM CONTROLLER
// ==========================================================================

import { API_BASE } from "./config.js";

export function initChatLLM() {
  const promptForm = document.querySelector("#prompt-form");
  const promptTextarea = document.querySelector("#prompt-textarea");
  const chatFeed = document.querySelector("#chat-feed");

  if (promptForm && promptTextarea) {
    promptForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = promptTextarea.value.trim();
      if (!text) return;

      appendChatMessage("NETRUNNER", text, "user-msg");
      promptTextarea.value = "";

      try {
        const res = await fetch(`${API_BASE}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: [{ role: "user", content: text }],
            model: "llama-3.3-70b"
          })
        });

        if (res.ok) {
          const data = await res.json();
          appendChatMessage("AI_CORE // CYBER-70B", data.response, "ai-msg");
        } else {
          appendChatMessage("SYSTEM_ERR", "Error procesando mensaje en backend.", "system-msg");
        }
      } catch (err) {
        appendChatMessage("SYSTEM_ERR", "Fallo de conexión al backend: " + err, "system-msg");
      }
    });

    // Enter to submit, Shift+Enter for new line
    promptTextarea.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        promptForm.dispatchEvent(new Event("submit"));
      }
    });
  }

  function appendChatMessage(sender, text, className) {
    if (!chatFeed) return;
    const msg = document.createElement("div");
    msg.className = `message-wrapper ${className}`;
    msg.innerHTML = `
      <div class="msg-header">
        <span class="avatar-title">${sender}</span>
      </div>
      <div class="msg-body"><p>${text}</p></div>
    `;
    chatFeed.appendChild(msg);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }
}
