import { getRole, setCase, setRole } from "./api-client.js";
import { initChatPanel, mountChat, openChat, resetAlerts, unmountChat } from "./chat-panel.js";
import { render as inbox } from "../views/inbox/inbox.js";
import { render as approval } from "../views/approval/approval.js";
import { render as alerts } from "../views/alerts/alerts.js";
import { render as status } from "../views/status/status.js";
import { render as knowledge } from "../views/knowledge/knowledge.js";
import { render as dashboard } from "../views/dashboard/dashboard.js";

const VIEWS = { inbox, dashboard, approval, alerts, status, knowledge };
const main = document.getElementById("view");
// ?mode=desktop is the Coworker window the desktop tray opens: the chat is its
// main view, with the other views one tab away.
const DESKTOP = new URLSearchParams(location.search).get("mode") === "desktop";
if (DESKTOP) {
  document.body.classList.add("desktop");
  const chatTab = document.createElement("button");
  chatTab.setAttribute("role", "tab");
  chatTab.dataset.view = "chat";
  chatTab.textContent = "Chat";
  document.querySelector(".tabs").prepend(chatTab);
  VIEWS.chat = (root, _show, caseId) => mountChat(root, caseId);
  document.addEventListener("chat-unread", (event) => {
    chatTab.textContent = event.detail ? `Chat (${event.detail})` : "Chat";
  });
}
const DEFAULT_VIEW = DESKTOP ? "chat" : "inbox";
// The desktop window keeps only what a person acts on from the tray.
const DESKTOP_VIEWS = ["chat", "dashboard", "approval", "status"];
if (DESKTOP) {
  document.querySelectorAll(".tabs button").forEach((tab) => {
    if (!DESKTOP_VIEWS.includes(tab.dataset.view)) tab.remove();
  });
}
const tabs = [...document.querySelectorAll(".tabs button")];
const roleSelect = document.getElementById("role");

export async function show(name) {
  // #status/<case id> or #chat/<case id> opens a case directly (desktop tray links).
  const [viewName, rawCase] = (name || DEFAULT_VIEW).split("/");
  const caseId = rawCase ? decodeURIComponent(rawCase) : undefined;
  if (caseId) setCase(caseId);
  // Outside the desktop window the chat is a panel over every view.
  if (viewName === "chat" && !DESKTOP) {
    openChat(caseId);
    name = "inbox";
  } else {
    name = viewName;
  }
  const allowed = !DESKTOP || DESKTOP_VIEWS.includes(name);
  const view = VIEWS[name] && allowed ? name : DEFAULT_VIEW;
  tabs.forEach((tab) => tab.setAttribute("aria-selected", String(tab.dataset.view === view)));
  if (location.hash !== `#${view}`) history.replaceState(null, "", `#${view}`);
  unmountChat();
  main.replaceChildren();
  main.classList.toggle("chat-main", view === "chat");
  await VIEWS[view](main, show, caseId);
}

tabs.forEach((tab) => tab.addEventListener("click", () => show(tab.dataset.view)));
// ?role=… comes from the desktop tray, so the app opens as the tray's role.
const linkedRole = new URLSearchParams(location.search).get("role");
if (linkedRole && [...roleSelect.options].some((o) => o.value === linkedRole)) setRole(linkedRole);
roleSelect.value = getRole();
roleSelect.addEventListener("change", () => {
  setRole(roleSelect.value);
  resetAlerts();
  show(location.hash.slice(1));
});
window.addEventListener("hashchange", () => show(location.hash.slice(1)));

initChatPanel(show);
show(location.hash.slice(1));
