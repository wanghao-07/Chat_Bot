const API_BASE = "";

const state = {
  sessionId: localStorage.getItem("chatbot_session_id") || null,
  messages: [],
  loading: false,
};

// 默认关闭知识库检索（无文档时无需 Embedding）
if (localStorage.getItem("rag_enabled") === null) {
  localStorage.setItem("rag_enabled", "0");
}

const $ = (sel) => document.querySelector(sel);

const messagesEl = $("#messages");
const chatForm = $("#chatForm");
const messageInput = $("#messageInput");
const sendBtn = $("#sendBtn");
const statusPill = $("#statusPill");
const ragToggle = $("#ragToggle");
function setRagToggle(enabled, hasDocs = false) {
  ragToggle.checked = enabled && hasDocs;
  ragToggle.disabled = !hasDocs;
  const label = $("#ragToggleLabel");
  if (label) {
    label.textContent = hasDocs
      ? "启用知识库检索"
      : "知识库检索（需先上传文档）";
  }
  if (!hasDocs) localStorage.setItem("rag_enabled", "0");
}
setRagToggle(localStorage.getItem("rag_enabled") === "1", false);
ragToggle.addEventListener("change", () => {
  if (!ragToggle.disabled) {
    localStorage.setItem("rag_enabled", ragToggle.checked ? "1" : "0");
  }
});
const newChatBtn = $("#newChatBtn");
const brandTitle = $("#brandTitle");

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    $(`#panel-${btn.dataset.panel}`).classList.add("active");
    if (btn.dataset.panel === "knowledge") loadDocuments();
    if (btn.dataset.panel === "settings") loadSettings();
  });
});

function setStatus(text, type = "") {
  statusPill.textContent = text;
  statusPill.className = "status-pill" + (type ? ` ${type}` : "");
}

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || data.detail || `请求失败 (${res.status})`);
  }
  return data;
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

function formatUserError(msg) {
  if (!msg) return "抱歉，服务暂时不可用，请稍后重试。";
  if (msg.includes("insufficient_quota") || msg.includes("额度") || msg.includes("service is busy") || msg.includes("频繁"))
    return "抱歉，API 调用受限。请取消勾选「启用知识库检索」，等待 1 分钟后重试；或在百炼控制台查看额度。";
  if (msg.includes("timeout") || msg.includes("超时"))
    return "抱歉，请求超时，请稍后重试。";
  if (msg.includes("Embedding") || msg.includes("向量"))
    return "抱歉，知识库检索失败。请先关闭「启用知识库检索」，或上传文档成功后再开启。";
  if (msg.length > 120) return "抱歉，服务异常，请检查 .env 配置并重启后重试。";
  return `抱歉，暂时无法回复：${msg}`;
}

function formatContent(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

function renderWelcome() {
  messagesEl.innerHTML = `
    <div class="welcome">
      <h3>您好，有什么可以帮您？</h3>
      <p>我是智能客服助手，可解答产品、订单与售后问题。</p>
      <div class="suggestions">
        <button type="button" data-q="你们的退款政策是什么？">退款政策</button>
        <button type="button" data-q="如何联系人工客服？">人工客服</button>
        <button type="button" data-q="配送需要多久？">配送时效</button>
      </div>
    </div>
  `;
  messagesEl.querySelectorAll(".suggestions button").forEach((btn) => {
    btn.addEventListener("click", () => {
      messageInput.value = btn.dataset.q;
      chatForm.requestSubmit();
    });
  });
}

function renderMessages() {
  if (!state.messages.length) {
    renderWelcome();
    return;
  }
  messagesEl.innerHTML = state.messages
    .map((m) => {
      const isUser = m.role === "user";
      let sourcesHtml = "";
      if (m.sources?.length) {
        const tags = m.sources
          .map((s) => `<span>${escapeHtml(s.doc_title || "文档")}</span>`)
          .join("");
        sourcesHtml = `<div class="msg-sources">参考：${tags}</div>`;
      }
      return `
        <div class="msg ${isUser ? "user" : "assistant"}${m.handoff ? " handoff" : ""}">
          <div class="msg-avatar">${isUser ? "我" : "AI"}</div>
          <div>
            <div class="msg-body">${formatContent(m.content)}</div>
            ${sourcesHtml}
          </div>
        </div>
      `;
    })
    .join("");
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendMessage(text) {
  if (!text.trim() || state.loading) return;
  state.loading = true;
  sendBtn.disabled = true;
  setStatus("思考中…", "loading");

  state.messages.push({ role: "user", content: text });
  renderMessages();

  try {
    const data = await api("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({
        message: text,
        session_id: state.sessionId,
        use_rag: ragToggle.checked,
      }),
    });
    state.sessionId = data.session_id;
    localStorage.setItem("chatbot_session_id", data.session_id);
    state.messages.push({
      role: "assistant",
      content: data.reply,
      sources: data.sources,
      handoff: data.handoff,
    });
    setStatus(data.handoff ? "建议转人工" : "就绪", data.handoff ? "error" : "");
  } catch (err) {
    state.messages.push({
      role: "assistant",
      content: formatUserError(err.message),
    });
    setStatus("出错", "error");
  } finally {
    state.loading = false;
    sendBtn.disabled = false;
    renderMessages();
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;
  messageInput.value = "";
  messageInput.style.height = "auto";
  sendMessage(text);
});

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.requestSubmit();
  }
});

messageInput.addEventListener("input", () => {
  messageInput.style.height = "auto";
  messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
});

newChatBtn.addEventListener("click", () => {
  state.sessionId = null;
  state.messages = [];
  localStorage.removeItem("chatbot_session_id");
  renderWelcome();
  setStatus("就绪");
  checkHealth();
});

const fileInput = $("#fileInput");
const uploadZone = $("#uploadZone");
const docList = $("#docList");

uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("dragover");
});
uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"));
uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) uploadFile(fileInput.files[0]);
});

async function uploadFile(file) {
  setStatus("上传中…", "loading");
  const form = new FormData();
  form.append("file", file);
  try {
    const res = await fetch(`${API_BASE}/api/v1/knowledge/documents`, {
      method: "POST",
      body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "上传失败");
    await loadDocuments();
    setStatus("就绪");
  } catch (err) {
    alert(err.message);
    setStatus("出错", "error");
  }
}

async function loadDocuments() {
  try {
    const docs = await api("/api/v1/knowledge/documents");
    if (!docs.length) {
      docList.innerHTML =
        '<li class="doc-item"><span class="meta">暂无文档，请上传知识库文件</span></li>';
      setRagToggle(false, false);
      return;
    }
    const ready = docs.some((d) => d.status === "ready");
    setRagToggle(ready && localStorage.getItem("rag_enabled") === "1", ready);
    docList.innerHTML = docs
      .map(
        (d) => `
        <li class="doc-item">
          <div>
            <strong>${escapeHtml(d.title)}</strong>
            <div class="meta">${escapeHtml(d.filename)} · ${d.chunk_count} 片段 · ${d.status}</div>
          </div>
          <button type="button" data-id="${d.id}">删除</button>
        </li>`
      )
      .join("");
    docList.querySelectorAll("button[data-id]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("确定删除该文档？")) return;
        await api(`/api/v1/knowledge/documents/${btn.dataset.id}`, { method: "DELETE" });
        loadDocuments();
      });
    });
  } catch (err) {
    docList.innerHTML = `<li class="doc-item"><span class="meta">加载失败: ${escapeHtml(err.message)}</span></li>`;
  }
}

const settingsForm = $("#settingsForm");

async function loadSettings() {
  try {
    const cfg = await api("/api/v1/config/prompt");
    $("#brandName").value = cfg.brand_name;
    $("#companyDesc").value = cfg.company_description;
    $("#promptTone").value = cfg.system_prompt_tone;
    $("#customPrompt").value = cfg.custom_system_prompt || "";
    $("#promptPreview").textContent = cfg.effective_prompt_preview;
    brandTitle.textContent = cfg.brand_name || "客服助手";
  } catch (err) {
    $("#promptPreview").textContent = "加载配置失败: " + err.message;
  }
}

settingsForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const cfg = await api("/api/v1/config/prompt", {
      method: "PUT",
      body: JSON.stringify({
        brand_name: $("#brandName").value,
        company_description: $("#companyDesc").value,
        system_prompt_tone: $("#promptTone").value,
        custom_system_prompt: $("#customPrompt").value,
      }),
    });
    $("#promptPreview").textContent = cfg.effective_prompt_preview;
    brandTitle.textContent = cfg.brand_name;
    alert("配置已保存");
  } catch (err) {
    alert(err.message);
  }
});

async function restoreSession() {
  if (!state.sessionId) {
    renderWelcome();
    return;
  }
  try {
    const session = await api(`/api/v1/sessions/${state.sessionId}`);
    state.messages = session.messages
      .filter((m) => m.role === "user" || m.role === "assistant")
      .map((m) => ({ role: m.role, content: m.content }));
    renderMessages();
  } catch {
    state.sessionId = null;
    localStorage.removeItem("chatbot_session_id");
    renderWelcome();
  }
}

async function checkHealth() {
  const banner = $("#apiBanner");
  try {
    const h = await api("/api/v1/health");
    if (!h.openai_configured) {
      setStatus("未配置 API Key", "error");
      banner.classList.remove("hidden");
      banner.textContent =
        "未检测到有效的 DASHSCOPE_API_KEY（通义千问）。请在项目根目录 .env 中配置后重启服务。";
    } else {
      banner.classList.add("hidden");
    }
    setRagToggle(localStorage.getItem("rag_enabled") === "1", h.documents_count > 0);
  } catch {
    setStatus("后端未连接", "error");
    banner.classList.remove("hidden");
    banner.textContent = "无法连接后端服务，请确认已运行 .\\run.ps1。";
  }
}

restoreSession();
checkHealth();
loadSettings();
