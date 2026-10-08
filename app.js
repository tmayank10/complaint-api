const tokenKey = "complaint_token";
const userKey = "complaint_user";
let mode = "login";

const authCard = document.getElementById("auth-card");
const desk = document.getElementById("desk");
const who = document.getElementById("who");
const logout = document.getElementById("logout");
const authErr = document.getElementById("auth-err");
const createErr = document.getElementById("create-err");
const list = document.getElementById("list");
const authSubmit = document.getElementById("auth-submit");

function token() {
  return localStorage.getItem(tokenKey) || "";
}

async function api(path, options = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
  if (token()) headers.Authorization = "Bearer " + token();
  const res = await fetch(path, Object.assign({}, options, { headers }));
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = data.detail || "request failed";
    throw new Error(typeof message === "string" ? message : "request failed");
  }
  return data;
}

function showDesk(username) {
  authCard.classList.add("hidden");
  desk.classList.remove("hidden");
  logout.classList.remove("hidden");
  who.textContent = username;
  loadComplaints();
}

function showAuth() {
  authCard.classList.remove("hidden");
  desk.classList.add("hidden");
  logout.classList.add("hidden");
  who.textContent = "";
}

document.getElementById("tab-login").onclick = () => setMode("login");
document.getElementById("tab-register").onclick = () => setMode("register");

function setMode(next) {
  mode = next;
  document.getElementById("tab-login").classList.toggle("on", mode === "login");
  document.getElementById("tab-register").classList.toggle("on", mode === "register");
  authSubmit.textContent = mode === "login" ? "Login" : "Create account";
  authErr.textContent = "";
}

document.getElementById("auth-form").onsubmit = async (event) => {
  event.preventDefault();
  authErr.textContent = "";
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  try {
    if (mode === "register") {
      await api("/register", { method: "POST", body: JSON.stringify({ username, password }) });
    }
    const data = await api("/login", { method: "POST", body: JSON.stringify({ username, password }) });
    localStorage.setItem(tokenKey, data.token);
    localStorage.setItem(userKey, username);
    showDesk(username);
  } catch (err) {
    authErr.textContent = err.message;
  }
};

logout.onclick = () => {
  localStorage.removeItem(tokenKey);
  localStorage.removeItem(userKey);
  showAuth();
};

document.getElementById("create-form").onsubmit = async (event) => {
  event.preventDefault();
  createErr.textContent = "";
  const body = {
    title: document.getElementById("title").value.trim(),
    description: document.getElementById("description").value.trim(),
    priority: document.getElementById("priority").value,
  };
  try {
    await api("/complaints", { method: "POST", body: JSON.stringify(body) });
    event.target.reset();
    loadComplaints();
  } catch (err) {
    createErr.textContent = err.message;
  }
};

async function loadComplaints() {
  const rows = await api("/complaints");
  if (!rows.length) {
    list.innerHTML = '<div class="empty">No tickets yet.</div>';
    return;
  }
  list.innerHTML = rows.map(renderTicket).join("");
  list.querySelectorAll("[data-status]").forEach((button) => {
    button.onclick = () => changeStatus(button.dataset.id, button.parentElement.querySelector("select").value);
  });
  list.querySelectorAll("[data-history]").forEach((button) => {
    button.onclick = () => toggleHistory(button.dataset.id);
  });
}

function renderTicket(row) {
  return `
    <article class="ticket" id="ticket-${row.id}">
      <div class="ticket-head">
        <div>
          <div class="title">${escapeHtml(row.title)}</div>
          <div class="meta">#${row.id} · ${escapeHtml(row.owner)} · ${escapeHtml(row.description)}</div>
        </div>
        <div class="badges">
          <span class="pill ${row.priority}">${row.priority}</span>
          <span class="pill ${row.status}">${row.status.replace("_", " ")}</span>
        </div>
      </div>
      <div class="row">
        <select>
          <option value="open">Open</option>
          <option value="in_progress">In progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
        <button class="btn small" data-status data-id="${row.id}" type="button">Update</button>
        <button class="linkish" data-history data-id="${row.id}" type="button">History</button>
      </div>
      <div class="history hidden" id="history-${row.id}"></div>
    </article>`;
}

async function changeStatus(id, status) {
  try {
    await api("/complaints/" + id + "/status", {
      method: "PATCH",
      body: JSON.stringify({ status, note: "updated from desk" }),
    });
    loadComplaints();
  } catch (err) {
    alert(err.message);
  }
}

async function toggleHistory(id) {
  const box = document.getElementById("history-" + id);
  if (!box.classList.contains("hidden")) {
    box.classList.add("hidden");
    return;
  }
  const rows = await api("/complaints/" + id + "/history");
  box.innerHTML = rows.map((item) =>
    `${escapeHtml(item.old_status)} → ${escapeHtml(item.new_status)} · ${escapeHtml(item.note || "no note")}`
  ).join("<br>");
  box.classList.remove("hidden");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&")
    .replaceAll("<", "<")
    .replaceAll(">", ">");
}

if (token() && localStorage.getItem(userKey)) {
  showDesk(localStorage.getItem(userKey));
}
