// The Coworker's chat as a floating panel, like a Teams chat (US-002, US-003, US-019).
// One conversation for the page. Alerts for the current role arrive in it too,
// with an unread badge on the launcher. Text only: never innerHTML.
import { api, el, errorNotice, getRole, setCase, STATE_LABELS } from "./api-client.js";

// Which simulated alerts each role receives in its chat.
const RECIPIENTS = {
  recruiter: ["Recruiter"],
  onboarding: ["Onboarding Team", "HR"],
  approver: ["Onboarding Supervisor"],
  it: ["IT"],
  ldc: ["LDC"],
};
const POLL_MS = 5000;
const SVG = "http://www.w3.org/2000/svg";

const state = {
  open: false,
  caseId: null,
  unread: 0,
  lastAlertId: null,
  messages: [{
    who: "bot",
    at: new Date(),
    text: "Hi! I am the Onboarding Coworker. Send me a new start (candidate ID and start date at least), " +
      "answer my questions about a case, or ask how one is going, for example: How is SYN-0043 doing?",
  }],
};
const ui = {};
let showView = () => {};

function icon(paths) {
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  for (const d of paths) {
    const path = document.createElementNS(SVG, "path");
    path.setAttribute("d", d);
    svg.append(path);
  }
  return svg;
}
const CHAT_ICON = ["M4 5h16v10H9l-5 4z"];
const SEND_ICON = ["M3 20l18-8L3 4v6l12 2-12 2z"];
const CLOSE_ICON = ["M6 6l12 12M18 6L6 18"];

function time(at) {
  return at.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function avatar(who) {
  const label = who === "me" ? getRole().slice(0, 2).toUpperCase() : "OC";
  return el("span", { class: `avatar${who === "me" ? " me" : ""}`, "aria-hidden": "true" }, label);
}

export function initChatPanel(show) {
  showView = show;
  ui.badge = el("span", { class: "badge", hidden: true });
  ui.launcher = el("button", {
    class: "chat-launcher", type: "button", "aria-label": "Open chat with the Onboarding Coworker",
    "aria-expanded": "false", onclick: () => (state.open ? closeChat() : openChat()),
  }, icon(CHAT_ICON), ui.badge);

  ui.caseSelect = el("select", { "aria-label": "Case in this conversation", onchange: () => pickCase(ui.caseSelect.value) });
  ui.log = el("div", { class: "chat-log", "aria-live": "polite" });
  ui.input = el("textarea", { rows: "1", maxlength: "4000", "aria-label": "Message", placeholder: "Type a message" });
  ui.send = el("button", { class: "icon-btn send", type: "submit", "aria-label": "Send" }, icon(SEND_ICON));
  ui.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      ui.form.requestSubmit();
    }
  });
  ui.input.addEventListener("input", grow);
  ui.form = el("form", { class: "chat-compose" }, ui.input, ui.send);
  ui.form.addEventListener("submit", (event) => { event.preventDefault(); sendMessage(); });

  ui.panel = el("section", { class: "chat-window", role: "dialog", "aria-label": "Chat with the Onboarding Coworker", hidden: true },
    el("header", { class: "chat-head" },
      avatar("bot"),
      el("div", { class: "chat-title" }, el("strong", {}, "Onboarding Coworker"), el("span", { class: "presence" }, "Available")),
      el("button", { class: "icon-btn", type: "button", "aria-label": "Close chat", onclick: closeChat }, icon(CLOSE_ICON))),
    el("div", { class: "chat-context" }, el("span", { class: "meta" }, "Case"), ui.caseSelect),
    ui.log,
    ui.form);
  ui.panel.addEventListener("keydown", (event) => { if (event.key === "Escape") closeChat(); });

  document.body.append(ui.panel, ui.launcher);
  draw();
  pollAlerts();
  setInterval(pollAlerts, POLL_MS);
}

function grow() {
  ui.input.style.height = "auto";
  ui.input.style.height = `${Math.min(ui.input.scrollHeight, 160)}px`;
}

// Desktop window: the chat is the main view, not a floating panel.
export async function mountChat(container, caseId) {
  ui.panel.classList.add("embedded");
  container.append(ui.panel);
  await openChat(caseId);
}

// Leaving the chat view puts the panel back, closed, for the floating mode.
export function unmountChat() {
  if (!ui.panel.classList.contains("embedded")) return;
  ui.panel.classList.remove("embedded");
  document.body.append(ui.panel);
  state.open = false;
  ui.panel.hidden = true;
}

export function unreadCount() {
  return state.unread;
}

export async function openChat(caseId) {
  state.open = true;
  state.unread = 0;
  ui.panel.hidden = false;
  ui.launcher.setAttribute("aria-expanded", "true");
  drawBadge();
  await loadCases();
  if (caseId && caseId !== state.caseId) await pickCase(caseId);
  draw();
  ui.input.focus();
}

function closeChat() {
  state.open = false;
  ui.panel.hidden = true;
  ui.launcher.setAttribute("aria-expanded", "false");
  ui.launcher.focus();
}

async function loadCases() {
  let cases = [];
  try {
    cases = await api.cases();
  } catch { /* the conversation still works without the list */ }
  ui.caseSelect.replaceChildren(
    el("option", { value: "" }, "New conversation"),
    ...cases.map((c) => el("option", { value: c.id }, `${c.person_ref} · ${STATE_LABELS[c.state] || c.state}`)));
  ui.caseSelect.value = state.caseId || "";
}

async function pickCase(caseId) {
  state.caseId = caseId || null;
  ui.caseSelect.value = caseId || "";
  if (!caseId) {
    push("bot", "New conversation. Send me a new start, or pick a case above.");
    return;
  }
  setCase(caseId);
  try {
    const view = await api.case(caseId);
    const next = view.questions[0];
    const name = view.case.person_ref;
    if (next) {
      const ask = next.kind === "missing"
        ? `What is the ${next.label}?`
        : `Two different values were given for ${next.label}. Which one is right?`;
      push("bot", `Back to ${name}. ${ask}`);
    } else {
      push("bot", `${name} is ${STATE_LABELS[view.case.state] || view.case.state}. Ask me anything about it.`);
    }
  } catch (error) {
    ui.log.append(errorNotice(error));
  }
}

function push(who, text, extra = {}) {
  state.messages.push({ who, text, at: new Date(), ...extra });
  draw();
}

async function sendMessage() {
  const text = ui.input.value.trim();
  if (!text) return;
  ui.input.value = "";
  grow();
  push("me", text);
  ui.send.disabled = true;
  state.typing = true;
  draw();
  try {
    const reply = await api.chat(text, state.caseId);
    if (reply.case_id) { state.caseId = reply.case_id; setCase(reply.case_id); }
    const action = reply.state === "ready_for_review" ? { view: "approval", label: "Open approval" } : null;
    state.typing = false;
    push("bot", reply.reply, { action });
    await loadCases();
  } catch (error) {
    state.typing = false;
    draw();
    ui.log.append(errorNotice(error));
  } finally {
    ui.send.disabled = false;
    ui.input.focus();
  }
}

function draw() {
  const rows = state.messages.map((m) => el("div", { class: `msg${m.who === "me" ? " me" : ""}${m.alert ? " alert" : ""}` },
    m.who === "me" ? null : avatar(m.who),
    el("div", { class: "msg-body" },
      el("div", { class: "msg-meta" }, m.who === "me" ? "You" : m.alert ? `Alert to ${m.alert}` : "Onboarding Coworker", " · ", time(m.at)),
      el("div", { class: "msg-text" }, m.text),
      m.action ? el("button", { class: "btn", type: "button", onclick: () => { closeChat(); showView(m.action.view); } }, m.action.label) : null,
      m.caseId ? el("button", { class: "btn", type: "button", onclick: () => pickCase(m.caseId) }, "Open this case") : null)));
  if (state.typing) {
    rows.push(el("div", { class: "msg" }, avatar("bot"),
      el("div", { class: "msg-body" }, el("div", { class: "typing", "aria-label": "The Coworker is typing" }, el("span"), el("span"), el("span")))));
  }
  ui.log.replaceChildren(...rows);
  ui.log.scrollTop = ui.log.scrollHeight;
}

function drawBadge() {
  document.dispatchEvent(new CustomEvent("chat-unread", { detail: state.unread }));
  ui.badge.hidden = state.unread === 0;
  ui.badge.textContent = state.unread > 9 ? "9+" : String(state.unread);
  ui.launcher.setAttribute("aria-label", state.unread
    ? `Open chat with the Onboarding Coworker, ${state.unread} new`
    : "Open chat with the Onboarding Coworker");
}

// New alerts for this role appear in the chat; until it is opened, the badge counts them.
export async function pollAlerts() {
  let alerts;
  try {
    alerts = await api.alerts();
  } catch {
    return;
  }
  const newest = alerts.reduce((max, a) => Math.max(max, a.id), 0);
  if (state.lastAlertId === null) {
    state.lastAlertId = newest;
    return;
  }
  const mine = new Set(RECIPIENTS[getRole()] || []);
  const fresh = alerts.filter((a) => a.id > state.lastAlertId && mine.has(a.recipient)).sort((a, b) => a.id - b.id);
  state.lastAlertId = Math.max(state.lastAlertId, newest);
  for (const alert of fresh) {
    state.messages.push({ who: "bot", text: alert.text, at: new Date(alert.at), alert: alert.recipient, caseId: alert.case_id });
  }
  if (!fresh.length) return;
  if (!state.open) state.unread += fresh.length;
  drawBadge();
  document.dispatchEvent(new CustomEvent("chat-unread", { detail: state.unread }));
  draw();
}

// A role change starts from that role's new alerts only.
export function resetAlerts() {
  state.lastAlertId = null;
  state.unread = 0;
  drawBadge();
  pollAlerts();
}
