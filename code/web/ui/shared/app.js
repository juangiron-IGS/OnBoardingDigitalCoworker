import { getRole, setCase, setRole } from "./api-client.js";
import { initChatPanel, openChat, resetAlerts } from "./chat-panel.js";
import { render as inbox } from "../views/inbox/inbox.js";
import { render as approval } from "../views/approval/approval.js";
import { render as alerts } from "../views/alerts/alerts.js";
import { render as status } from "../views/status/status.js";
import { render as knowledge } from "../views/knowledge/knowledge.js";
import { render as dashboard } from "../views/dashboard/dashboard.js";

const VIEWS = { inbox, dashboard, approval, alerts, status, knowledge };
const main = document.getElementById("view");
const tabs = [...document.querySelectorAll(".tabs button")];
const roleSelect = document.getElementById("role");

export async function show(name) {
  // The chat is a panel over every view; #chat opens it over the inbox.
  if (name === "chat") {
    openChat();
    name = "inbox";
  }
  // #status/<case id> opens a case directly, as the desktop tray's links do.
  const [viewName, caseId] = name.split("/");
  if (caseId) setCase(decodeURIComponent(caseId));
  name = viewName;
  const view = VIEWS[name] ? name : "inbox";
  tabs.forEach((tab) => tab.setAttribute("aria-selected", String(tab.dataset.view === view)));
  if (location.hash !== `#${view}`) history.replaceState(null, "", `#${view}`);
  main.replaceChildren();
  await VIEWS[view](main, show);
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
