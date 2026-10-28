import { el } from "./api-client.js";

// Every alert that asks a team to act opens a popup: who it is for, which step of
// the flow it is, what is needed, and a button that takes that team to the case.
// Approvals still happen in the views, under the same role checks (BR-002).
const STEPS = {
  Recruiter: { role: "recruiter", team: "Recruiter", step: "Intake · complete the start data", cta: "Answer in the chat", view: "chat" },
  // An FLSA conflict is decided by HR and recorded in Approval; documents and payroll are in Status.
  "Onboarding Team": { role: "onboarding", team: "Onboarding Team", step: "Follow-up · documents, payroll or an HR decision", cta: "Open as Onboarding Team",
    view: (text) => (/differs|HR/.test(text) ? "approval" : "status") },
  "Onboarding Supervisor": { role: "approver", team: "Approver (Consultant Onboarding Supervisor)", step: "Approval gate · assign the owner and decide on the package", cta: "Open as Approver", view: "approval" },
  IT: { role: "it", team: "IT", step: "Equipment · approve the laptop and access request", cta: "Open as IT", view: "approval" },
  LDC: { role: "ldc", team: "LDC (Culture and Belonging)", step: "Culture and Belonging · welcome kit and leader messages", cta: "Open as LDC", view: "approval" },
};
const DESKTOP = new URLSearchParams(location.search).get("mode") === "desktop";
const queue = [];
let dialog = null;

/** Queue a popup for each alert that asks a team to act. The desktop window shows
 * only its own role's; the web app shows every team's, so the demo can follow the
 * flow from one team to the next. */
export function popupsFor(alerts, role) {
  for (const alert of alerts) {
    const step = STEPS[alert.recipient];
    if (!step) continue;
    if (alert.recipient === "Onboarding Supervisor") {
      // A new package first goes through the Onboarding Team's review of path and paperwork.
      const review = { role: "onboarding", team: "Onboarding Team", step: "Review · confirm or change the path and paperwork", cta: "Review the package", view: "approval" };
      if (!DESKTOP || role === review.role) queue.push({ alert: { ...alert, text: `Package ready. ${alert.text}` }, step: review });
    }
    if (DESKTOP && step.role !== role) continue;
    queue.push({ alert, step });
  }
  if (!dialog?.open) next();
}

function next() {
  const item = queue.shift();
  if (!item) return;
  const { alert, step } = item;
  if (!dialog) {
    dialog = el("dialog", { class: "action-popup", "aria-labelledby": "action-popup-title" });
    document.body.append(dialog);
    dialog.addEventListener("close", () => setTimeout(next, 150));
  }
  const go = () => {
    dialog.close();
    const select = document.getElementById("role");
    const view = typeof step.view === "function" ? step.view(alert.text) : step.view;
    history.replaceState(null, "", `#${view}/${encodeURIComponent(alert.case_id)}`);
    if (select.value !== step.role) {
      select.value = step.role;
      select.dispatchEvent(new Event("change"));
    } else {
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    }
  };
  dialog.replaceChildren(
    el("p", { class: "action-popup-for" }, "Message for: ", el("strong", { id: "action-popup-title" }, step.team)),
    el("p", { class: "action-popup-step" }, step.step),
    el("p", { class: "action-popup-text" }, alert.text),
    el("div", { class: "actions" },
      el("button", { class: "btn primary", type: "button", onclick: go }, step.cta),
      el("button", { class: "btn", type: "button", onclick: () => dialog.close() }, queue.length ? `Later (${queue.length} more)` : "Later")),
  );
  dialog.showModal();
}
