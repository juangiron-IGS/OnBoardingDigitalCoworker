import { getRole, setRole } from "./api-client.js";
import { initChatPanel, openChat, resetAlerts } from "./chat-panel.js";
import { render as inbox } from "../views/inbox/inbox.js";
import { render as approval } from "../views/approval/approval.js";
import { render as alerts } from "../views/alerts/alerts.js";
import { render as status } from "../views/status/status.js";
import { render as knowledge } from "../views/knowledge/knowledge.js";

const VIEWS = { inbox, approval, alerts, status, knowledge };
const main = document.getElementById("view");
const tabs = [...document.querySelectorAll(".tabs button")];
const roleSelect = document.getElementById("role");

export async function show(name) {
  // The chat is a panel over every view; #chat opens it over the inbox.
  if (name === "chat") {
    openChat();
    name = "inbox";
  }
  const view = VIEWS[name] ? name : "inbox";
  tabs.forEach((tab) => tab.setAttribute("aria-selected", String(tab.dataset.view === view)));
  if (location.hash !== `#${view}`) history.replaceState(null, "", `#${view}`);
  main.replaceChildren();
  await VIEWS[view](main, show);
}

tabs.forEach((tab) => tab.addEventListener("click", () => show(tab.dataset.view)));
roleSelect.value = getRole();
roleSelect.addEventListener("change", () => {
  setRole(roleSelect.value);
  resetAlerts();
  show(location.hash.slice(1));
});
window.addEventListener("hashchange", () => show(location.hash.slice(1)));

initChatPanel(show);
show(location.hash.slice(1));
