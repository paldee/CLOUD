const apiBaseUrl = document
  .querySelector('meta[name="api-base-url"]')
  .content.replace(/\/$/, "");

const form = document.querySelector("#ask-form");
const input = document.querySelector("#question");
const sendButton = document.querySelector("#send-button");
const conversation = document.querySelector("#conversation");
const welcome = document.querySelector("#welcome");
const connection = document.querySelector("#connection");
const connectionLabel = document.querySelector("#connection-label");
const userTemplate = document.querySelector("#user-message-template");
const assistantTemplate = document.querySelector("#assistant-message-template");

const statusLabels = {
  answered: "สำเร็จ",
  rejected: "ไม่ผ่าน Guardrail",
  not_configured: "รอตั้งค่าระบบ",
};

function setConnection(state, label) {
  connection.dataset.state = state;
  connectionLabel.textContent = label;
}

async function checkHealth() {
  try {
    const response = await fetch(`${apiBaseUrl}/health`);
    if (!response.ok) throw new Error("Backend unavailable");
    setConnection("online", "ระบบพร้อมใช้งาน");
  } catch {
    setConnection("offline", "ไม่พบ Backend");
  }
}

function appendUserMessage(question) {
  const message = userTemplate.content.cloneNode(true);
  message.querySelector(".message-text").textContent = question;
  conversation.append(message);
}

function appendAssistantMessage(result) {
  const message = assistantTemplate.content.cloneNode(true);
  const badge = message.querySelector(".status-badge");
  const sqlPanel = message.querySelector(".sql-panel");
  const violations = message.querySelector(".violations");
  const sources = message.querySelector(".sources");

  message.querySelector(".message-text").textContent = result.answer;
  badge.textContent = statusLabels[result.status] || result.status;
  badge.dataset.status = result.status;

  if (result.sql) {
    sqlPanel.hidden = false;
    sqlPanel.querySelector("code").textContent = result.sql;
  }

  if (result.guardrail_violations?.length) {
    violations.hidden = false;
    const list = violations.querySelector("ul");
    result.guardrail_violations.forEach((violation) => {
      const item = document.createElement("li");
      item.textContent = violation;
      list.append(item);
    });
  }

  if (result.sources?.length) {
    sources.hidden = false;
    sources.textContent = `แหล่งข้อมูล: ${result.sources.join(", ")}`;
  }

  conversation.append(message);
}

function appendErrorMessage(messageText) {
  appendAssistantMessage({
    answer: messageText,
    status: "rejected",
    sql: null,
    sources: [],
    guardrail_violations: [],
  });
}

function setLoading(isLoading) {
  input.disabled = isLoading;
  sendButton.disabled = isLoading;
  sendButton.querySelector("span").textContent = isLoading ? "กำลังประมวลผล" : "ส่งคำถาม";
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
}

async function askQuestion(question) {
  setLoading(true);
  try {
    const response = await fetch(`${apiBaseUrl}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, user_role: "analyst" }),
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    appendAssistantMessage(await response.json());
  } catch {
    appendErrorMessage("เชื่อมต่อระบบไม่ได้ กรุณาตรวจสอบว่า Backend กำลังทำงานอยู่");
    setConnection("offline", "ไม่พบ Backend");
  } finally {
    setLoading(false);
    conversation.scrollTo({ top: conversation.scrollHeight, behavior: "smooth" });
    input.focus();
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;

  welcome?.remove();
  appendUserMessage(question);
  input.value = "";
  resizeInput();
  await askQuestion(question);
});

input.addEventListener("input", resizeInput);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.question;
    resizeInput();
    input.focus();
  });
});

checkHealth();
