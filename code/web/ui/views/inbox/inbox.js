import { api, el, errorNotice, setCase, statePill } from "../../shared/api-client.js";
import { openChat, pollAlerts } from "../../shared/chat-panel.js";

const OUTCOME = {
  ready_for_review: ["ok", "Complete and consistent. The package is ready for the approver."],
  needs_clarification: ["warn", "Something is missing or contradictory. The recruiter was alerted with the exact fields."],
  blocked_duplicate: ["bad", "Blocked: a case for the same person and start date already exists."],
  needs_sender: ["bad", "The candidate or start date could not be read. The sender must confirm them."],
};
const MAILBOX_ADDRESS = "onboarding@inspyr.example";

// Invented names only: the demo never uses real candidate data.
function sampleName() {
  const first = ["Alex", "Casey", "Jamie", "Morgan", "Riley", "Taylor"];
  const last = ["Example", "Sample", "Synthetic", "Demo"];
  const pick = (list) => list[Math.floor(Math.random() * list.length)];
  return `${pick(first)} ${pick(last)}`;
}

// A new start with two fields missing, so the chat has something to ask.
function sampleStart() {
  const id = `SYN-${String(100 + Math.floor(Math.random() * 900)).padStart(4, "0")}`;
  return {
    subject: `New start - ${id} - QA Engineer`,
    body: `Hi team, new start below. Synthetic data for the demo.

Candidate ID: ${id}
Candidate name: ${sampleName()}
Position: QA Engineer
Hiring manager: Lee Example
Start date: 2026-12-14
Client: Acme Synthetic
Client type: Enterprise
Division: Digital
Line of business: Professional Services
Employment type: W-2
Vendor company: INSPYR Solutions
Work arrangement: Hybrid
Pay rate: 40.00 USD/h
Work city: Los Angeles
Work state: CA
FLSA: Non-exempt
Billing contact: billing.acme@example.com
Equipment: Standard laptop, INSPYR
Sponsorship: No

Thanks, Sam`,
  };
}

export async function render(root, show) {
  const compose = el("button", { class: "btn primary", type: "button" }, "New email");
  root.append(
    el("div", { class: "view-head" },
      el("div", {}, el("h1", {}, "Simulated inbox"),
        el("p", { class: "lead" }, `The onboarding mailbox (${MAILBOX_ADDRESS}). Send a new start email, or simulate one of the synthetic emails arriving. The Coworker processes each one as it arrives.`)),
      compose),
  );
  const result = el("div");
  const list = el("div", { class: "list" });
  root.append(result, el("section", { class: "card" }, el("h2", {}, "Mailbox"), list));

  const report = (outcome) => {
    const [tone, text] = OUTCOME[outcome.state] || ["warn", outcome.state];
    const next = outcome.case_id
      ? el("button", { class: "btn", onclick: () => {
          setCase(outcome.case_id);
          if (outcome.state === "needs_clarification") openChat(outcome.case_id);
          else show("approval");
        } }, outcome.state === "needs_clarification" ? "Answer in chat" : "Open approval")
      : null;
    result.replaceChildren(el("div", { class: `notice ${tone}`, role: "status" },
      el("div", { class: "actions" }, statePill(outcome.state), outcome.label ? el("strong", {}, outcome.label) : null),
      el("p", {}, text, outcome.blocked_by ? ` Existing case: ${outcome.label || outcome.blocked_by}.` : ""),
      next));
  };

  compose.addEventListener("click", () => openCompose(async (outcome, subject) => {
    toast(`New email in the onboarding mailbox: ${subject}`);
    report(outcome);
    pollAlerts();
    await drawList(list, report, show);
  }));
  await drawList(list, report, show);
}

async function drawList(list, report, show) {
  let messages;
  try {
    messages = await api.inbox();
  } catch (error) {
    list.replaceChildren(errorNotice(error));
    return;
  }
  list.replaceChildren(...messages.map((message) => {
    const arrived = message.received_at
      ? `${message.from} · received ${new Date(message.received_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
      : message.from;
    let action;
    if (message.received_at) {
      action = el("div", { class: "actions" },
        message.outcome ? statePill(message.outcome) : null,
        message.case_id ? el("button", { class: "btn", onclick: () => { setCase(message.case_id); show("status"); } }, "Open case") : null);
    } else {
      action = el("button", { class: "btn primary" }, "Simulate arrival");
      action.addEventListener("click", async () => {
        action.disabled = true;
        try {
          report(await api.process(message.id));
        } catch (error) {
          list.prepend(errorNotice(error));
        } finally {
          action.disabled = false;
        }
      });
    }
    return el("div", { class: `row${message.received_at ? " new-mail" : ""}` },
      el("div", {}, el("div", {}, message.subject), el("div", { class: "meta" }, arrived)), action);
  }));
}

// An Outlook-like compose window. Sends only to the simulated mailbox.
function openCompose(onSent) {
  const from = el("input", { type: "email", required: true, maxlength: "254", value: "recruiter.sam@example.com" });
  const subject = el("input", { type: "text", required: true, maxlength: "200" });
  const body = el("textarea", { required: true, maxlength: "8000", rows: "10" });
  const feedback = el("div");
  const send = el("button", { class: "btn primary", type: "submit" }, "Send");
  const dialog = el("dialog", { class: "compose", "aria-label": "New email" });
  const fill = () => { const s = sampleStart(); subject.value = s.subject; body.value = s.body; };
  const form = el("form", { method: "dialog" },
    el("h2", {}, "New email"),
    el("label", { class: "field" }, el("span", {}, "From"), from),
    el("label", { class: "field" }, el("span", {}, "To"), el("input", { type: "text", value: MAILBOX_ADDRESS, readonly: true })),
    el("label", { class: "field" }, el("span", {}, "Subject"), subject),
    el("label", { class: "field" }, el("span", {}, "Message"), body),
    el("p", { class: "meta" }, "Synthetic data only. Write the start as 'Label: value' lines."),
    feedback,
    el("div", { class: "actions" }, send,
      el("button", { class: "btn", type: "button", onclick: fill }, "Insert a sample start"),
      el("button", { class: "btn", type: "button", onclick: () => dialog.close() }, "Cancel")));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    send.disabled = true;
    feedback.replaceChildren();
    try {
      const outcome = await api.sendEmail(from.value.trim(), subject.value.trim(), body.value);
      dialog.close();
      await onSent(outcome, subject.value.trim());
    } catch (error) {
      feedback.replaceChildren(errorNotice(error));
    } finally {
      send.disabled = false;
    }
  });
  dialog.append(form);
  dialog.addEventListener("close", () => dialog.remove());
  document.body.append(dialog);
  fill();
  dialog.showModal();
  subject.focus();
}

function toast(text) {
  const note = el("div", { class: "toast", role: "status" }, text);
  document.body.append(note);
  setTimeout(() => note.remove(), 4000);
}
