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

function getAppLang() {
  return localStorage.getItem("language") || "th";
}

const statusLabels = {
  th: {
    answered: "สำเร็จ",
    rejected: "ไม่ผ่าน Guardrail",
    not_configured: "รอตั้งค่าระบบ",
    database_error: "ฐานข้อมูลออฟไลน์",
  },
  en: {
    answered: "Success",
    rejected: "Guardrail Rejected",
    not_configured: "Not Configured",
    database_error: "Database Offline",
  }
};
let processingTimer = null;
let processingStartedAt = null;
const chartColors = ["#176b45", "#d19a24", "#c95f45"];

window.__healthDetails = [];

function updateConnectionText() {
  const lang = getAppLang();
  if (connection.dataset.state === "online") {
    const prefix = lang === "en" ? "System Ready" : "ระบบพร้อมใช้งาน";
    const details = window.__healthDetails;
    connectionLabel.textContent = details && details.length ? `${prefix} (${details.join(" | ")})` : prefix;
  } else if (connection.dataset.state === "offline") {
    connectionLabel.textContent = lang === "en" ? "Backend Offline" : "ไม่พบ Backend";
  } else {
    connectionLabel.textContent = lang === "en" ? "Checking System..." : "กำลังตรวจสอบระบบ";
  }
}
window.updateConnectionText = updateConnectionText;

function setConnection(state, details) {
  connection.dataset.state = state;
  if (details !== undefined) {
    window.__healthDetails = details;
  }
  updateConnectionText();
}

async function checkHealth() {
  try {
    const response = await fetch(`${apiBaseUrl}/health`);
    if (!response.ok) throw new Error("Backend unavailable");
    const data = await response.json();
    const details = [];
    if (data.llm_provider) {
      const providerLabel = data.llm_model ? `${data.llm_provider.toUpperCase()}: ${data.llm_model}` : data.llm_provider.toUpperCase();
      details.push(providerLabel);
    }
    if (data.database_source && data.database_source !== "none") {
      details.push(data.database_source);
    }
    setConnection("online", details);
  } catch {
    setConnection("offline", []);
  }
}

function appendUserMessage(question) {
  const message = userTemplate.content.cloneNode(true);
  message.querySelector(".message-text").textContent = question;
  conversation.append(message);
}

function appendInlineMarkdown(element, text) {
  const tokenPattern = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let cursor = 0;

  for (const match of text.matchAll(tokenPattern)) {
    element.append(document.createTextNode(text.slice(cursor, match.index)));
    const token = match[0];
    const formatted = document.createElement(token.startsWith("**") ? "strong" : "code");
    formatted.textContent = token.startsWith("**") ? token.slice(2, -2) : token.slice(1, -1);
    element.append(formatted);
    cursor = match.index + token.length;
  }

  element.append(document.createTextNode(text.slice(cursor)));
}

function renderAnswer(element, markdown) {
  element.replaceChildren();
  let activeList = null;

  for (const rawLine of markdown.replace(/\r\n?/g, "\n").split("\n")) {
    const line = rawLine.trim();
    if (!line) {
      activeList = null;
      continue;
    }

    const heading = line.match(/^#{1,3}\s+(.+)$/) || line.match(/^\*\*(.+)\*\*$/);
    if (heading) {
      activeList = null;
      const title = document.createElement("h3");
      appendInlineMarkdown(title, heading[1]);
      element.append(title);
      continue;
    }

    const unorderedItem = line.match(/^[-*]\s+(.+)$/);
    const orderedItem = line.match(/^\d+[.)]\s+(.+)$/);
    const item = unorderedItem || orderedItem;
    if (item) {
      const listTag = orderedItem ? "OL" : "UL";
      if (!activeList || activeList.tagName !== listTag) {
        activeList = document.createElement(listTag.toLowerCase());
        element.append(activeList);
      }
      const listItem = document.createElement("li");
      appendInlineMarkdown(listItem, item[1]);
      activeList.append(listItem);
      continue;
    }

    activeList = null;
    const paragraph = document.createElement("p");
    appendInlineMarkdown(paragraph, line);
    element.append(paragraph);
  }
}

function renderVisualization(panel, visualization) {
  if (!visualization?.datasets?.length || !window.Chart) return;

  panel.hidden = false;
  const caption = panel.querySelector("figcaption");
  const displayedPoints = visualization.labels.length;
  if (visualization.total_points > displayedPoints) {
    caption.hidden = false;
    caption.textContent = `แสดง ${displayedPoints} จาก ${visualization.total_points} จุดข้อมูล`;
  }

  const datasets = visualization.datasets.map((dataset, index) => ({
    ...dataset,
    borderColor: chartColors[index % chartColors.length],
    backgroundColor: `${chartColors[index % chartColors.length]}cc`,
    borderWidth: 2,
    borderRadius: visualization.type === "bar" ? 3 : 0,
    pointRadius: visualization.type === "line" ? 3 : 0,
    pointHoverRadius: visualization.type === "line" ? 5 : 0,
    tension: visualization.type === "line" ? 0.25 : 0,
  }));

  new window.Chart(panel.querySelector("canvas"), {
    type: visualization.type,
    data: { labels: visualization.labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          display: datasets.length > 1,
          position: "bottom",
        },
        tooltip: {
          callbacks: {
            label(context) {
              const value = Number(context.raw);
              return `${context.dataset.label}: ${value.toLocaleString("th-TH", {
                maximumFractionDigits: 2,
              })}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { maxRotation: 45, minRotation: 0 },
        },
        y: {
          beginAtZero: visualization.type === "bar",
          ticks: {
            callback(value) {
              return Number(value).toLocaleString("th-TH", {
                notation: "compact",
                maximumFractionDigits: 1,
              });
            },
          },
        },
      },
    },
  });
}

function formatDuration(durationMs) {
  return getAppLang() === "en" ? `${(durationMs / 1000).toFixed(1)}s` : `${(durationMs / 1000).toFixed(1)} วินาที`;
}

function appendAssistantMessage(result, durationMs) {
  const message = assistantTemplate.content.cloneNode(true);
  const badge = message.querySelector(".status-badge");
  const sqlPanel = message.querySelector(".sql-panel");
  const violations = message.querySelector(".violations");
  const chartPanel = message.querySelector(".chart-panel");
  const sources = message.querySelector(".sources");
  const responseTime = message.querySelector(".response-time");
  const lang = getAppLang();

  renderAnswer(message.querySelector(".message-text"), result.answer);
  badge.textContent = (statusLabels[lang] && statusLabels[lang][result.status]) || result.status;
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
    sources.textContent = lang === "en" ? `Sources: ${result.sources.join(", ")}` : `แหล่งข้อมูล: ${result.sources.join(", ")}`;
  }

  if (Number.isFinite(durationMs)) {
    responseTime.hidden = false;
    responseTime.textContent = lang === "en" ? `Response time: ${formatDuration(durationMs)}` : `ใช้เวลา ${formatDuration(durationMs)}`;
  }

  conversation.append(message);
  renderVisualization(chartPanel, result.visualization);
}

function appendErrorMessage(messageText, durationMs) {
  appendAssistantMessage({
    answer: messageText,
    status: "rejected",
    sql: null,
    sources: [],
    guardrail_violations: [],
  }, durationMs);
}

function setLoading(isLoading) {
  input.disabled = isLoading;
  sendButton.disabled = isLoading;
  const label = sendButton.querySelector("span");
  const lang = getAppLang();

  if (processingTimer) {
    window.clearInterval(processingTimer);
    processingTimer = null;
  }

  if (!isLoading) {
    processingStartedAt = null;
    label.textContent = lang === "en" ? "Send Question" : "ส่งคำถาม";
    return;
  }

  processingStartedAt = performance.now();
  const updateTimer = () => {
    const elapsedSeconds = Math.floor((performance.now() - processingStartedAt) / 1000);
    const minutes = Math.floor(elapsedSeconds / 60);
    const seconds = String(elapsedSeconds % 60).padStart(2, "0");
    label.textContent = lang === "en" ? `Processing ${minutes}:${seconds}` : `กำลังประมวลผล ${minutes}:${seconds}`;
  };
  updateTimer();
  processingTimer = window.setInterval(updateTimer, 1000);
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
}

async function askQuestion(question) {
  const startedAt = performance.now();
  setLoading(true);
  try {
    let userRole = "analyst";
    try {
      const stored = JSON.parse(localStorage.getItem("currentUser") || "{}");
      if (stored.role) userRole = stored.role.toLowerCase();
    } catch {}

    const response = await fetch(`${apiBaseUrl}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, user_role: userRole }),
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    appendAssistantMessage(await response.json(), performance.now() - startedAt);
  } catch {
    const lang = getAppLang();
    appendErrorMessage(
      lang === "en" ? "Unable to connect to system. Please check if Backend is running." : "เชื่อมต่อระบบไม่ได้ กรุณาตรวจสอบว่า Backend กำลังทำงานอยู่",
      performance.now() - startedAt,
    );
    setConnection("offline", []);
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
    const lang = getAppLang();
    input.value = (lang === "en" && button.dataset.questionEn) ? button.dataset.questionEn : (button.dataset.questionTh || button.dataset.question);
    resizeInput();
    input.focus();
  });
});

checkHealth();
