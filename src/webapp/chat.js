// src/webapp/chat.js
document.addEventListener("DOMContentLoaded", () => {
  const messages = document.getElementById("messages");
  const input = document.getElementById("input");
  const sendBtn = document.getElementById("send");

  if (!messages || !input || !sendBtn) {
    console.error("Elementos do chat não encontrados no DOM.");
    return;
  }

  // função para adicionar mensagem (renderiza Markdown via marked.js)
  function addMessage(role, text) {
    const div = document.createElement("div");
    div.className = "message " + role;
    // segurança mínima: marked -> produz HTML; assumimos trusted source (modelo)
    div.innerHTML = marked.parse(text);
    messages.appendChild(div);
    // rolar a página inteira até o elemento (já que o scroll é da página)
    div.scrollIntoView({ behavior: "smooth", block: "end" });
  }

  // adiciona um indicador simples de "aguarde"
  function setSending(isSending) {
    sendBtn.disabled = isSending;
    if (isSending) sendBtn.style.opacity = "0.7";
    else sendBtn.style.opacity = "1";
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    // adicionar mensagem do usuário
    addMessage("user", text);
    input.value = "";
    input.focus();

    setSending(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });

      const data = await res.json();

      if (res.ok && data.reply) {
        addMessage("bot", data.reply);
      } else {
        // mostra erro vindo do backend ou do parsing
        const err = data.error || "Resposta inválida do servidor";
        addMessage("bot", `**Erro:** ${err}`);
        console.error("Resposta inválida:", data);
      }
    } catch (err) {
      addMessage("bot", `**Erro de rede:** ${err.message}`);
      console.error("Erro fetch:", err);
    } finally {
      setSending(false);
    }
  }

  // clique no botão enviar
  sendBtn.addEventListener("click", (e) => {
    e.preventDefault();
    sendMessage();
  });

  // Enter envia — permite Shift+Enter para quebra de linha
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // foco inicial
  input.focus();
});
