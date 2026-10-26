import { getRole, setRole } from "./api-client.js";
import { render as inbox } from "../views/inbox/inbox.js";
import { render as chat } from "../views/chat/chat.js";
import { render as approval } from "../views/approval/approval.js";
import { render as alerts } from "../views/alerts/alerts.js";
import { render as status } from "../views/status/status.js";

const VIEWS = { inbox, chat, approval, alerts, status };
const main = document.getElementById("view");
const tabs = [...document.querySelectorAll(".tabs button")];
const roleSelect = document.getElementById("role");

export async function show(name) {
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
  show(location.hash.slice(1));
});
window.addEventListener("hashchange", () => show(location.hash.slice(1)));

show(location.hash.slice(1));
