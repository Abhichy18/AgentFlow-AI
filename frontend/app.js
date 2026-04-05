const apiBaseUrlEl = document.getElementById("apiBaseUrl");
const userIdEl = document.getElementById("userId");
const goalTextEl = document.getElementById("goalText");
const executeBtnEl = document.getElementById("executeBtn");
const healthBtnEl = document.getElementById("healthBtn");

const statusLineEl = document.getElementById("statusLine");
const summaryBoxEl = document.getElementById("summaryBox");
const tasksBoxEl = document.getElementById("tasksBox");
const scheduleBoxEl = document.getElementById("scheduleBox");
const rawJsonEl = document.getElementById("rawJson");

if (!apiBaseUrlEl.value.trim()) {
  apiBaseUrlEl.value = window.location.origin;
}

function setStatus(message, type) {
  statusLineEl.textContent = message;
  statusLineEl.className = `status ${type}`;
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function renderTasks(tasks) {
  if (!Array.isArray(tasks) || tasks.length === 0) {
    tasksBoxEl.textContent = "No tasks returned.";
    return;
  }

  tasksBoxEl.innerHTML = tasks
    .map(
      (task) =>
        `<div class="item"><p class="item-title">${task.title || "Untitled"}</p><p class="item-sub">${task.description || "No description"}</p><p class="item-sub">Priority: ${task.priority || "n/a"} | Duration: ${task.estimated_minutes || "n/a"} min</p></div>`
    )
    .join("");
}

function renderSchedule(events) {
  if (!Array.isArray(events) || events.length === 0) {
    scheduleBoxEl.textContent = "No schedule returned.";
    return;
  }

  scheduleBoxEl.innerHTML = events
    .map(
      (event) =>
        `<div class="item"><p class="item-title">${event.task_title || "Untitled task"}</p><p class="item-sub">Slot: ${event.slot || "n/a"}</p><p class="item-sub">Duration: ${event.duration_min || "n/a"} min</p></div>`
    )
    .join("");
}

function renderSummary(data) {
  const summary = data?.planner_diagnostics_summary || {};
  const model = summary.successful_model || data?.planner_model_used || "unknown";
  const attempts = summary.total_attempts ?? "n/a";
  const mode = data?.planner_mode || "unknown";

  summaryBoxEl.innerHTML =
    `<strong>Mode:</strong> ${mode}<br>` +
    `<strong>Model:</strong> ${model}<br>` +
    `<strong>Total Attempts:</strong> ${attempts}`;
}

async function executeGoal() {
  const baseUrl = apiBaseUrlEl.value.trim().replace(/\/+$/, "");
  const userId = Number(userIdEl.value || 1);
  const goalText = goalTextEl.value.trim();

  if (!baseUrl || !goalText) {
    setStatus("Please fill API URL and goal text.", "error");
    return;
  }

  setStatus("Executing goal...", "loading");
  executeBtnEl.disabled = true;

  try {
    const response = await fetch(`${baseUrl}/api/v1/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, goal_text: goalText })
    });

    const text = await response.text();
    const data = safeJson(text) || { raw: text };

    rawJsonEl.textContent = JSON.stringify(data, null, 2);

    if (!response.ok) {
      setStatus(`Execute failed (${response.status}).`, "error");
      return;
    }

    renderSummary(data);
    renderTasks(data.task_breakdown);
    renderSchedule(data.scheduled_events);
    setStatus("Execution success.", "success");
  } catch (err) {
    setStatus(`Network error: ${err.message}`, "error");
  } finally {
    executeBtnEl.disabled = false;
  }
}

async function checkHealth() {
  const baseUrl = apiBaseUrlEl.value.trim().replace(/\/+$/, "");
  if (!baseUrl) {
    setStatus("Please enter API URL.", "error");
    return;
  }

  setStatus("Checking health...", "loading");
  healthBtnEl.disabled = true;

  try {
    const response = await fetch(`${baseUrl}/health`);
    const text = await response.text();
    const data = safeJson(text) || { raw: text };
    rawJsonEl.textContent = JSON.stringify(data, null, 2);

    if (!response.ok) {
      setStatus(`Health check failed (${response.status}).`, "error");
      return;
    }

    setStatus("Health check success.", "success");
  } catch (err) {
    setStatus(`Network error: ${err.message}`, "error");
  } finally {
    healthBtnEl.disabled = false;
  }
}

executeBtnEl.addEventListener("click", executeGoal);
healthBtnEl.addEventListener("click", checkHealth);
