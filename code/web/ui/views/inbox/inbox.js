import { api, el, errorNotice, setCase, statePill } from "../../shared/api-client.js";

const OUTCOME = {
  ready_for_review: ["ok", "Complete and consistent. The package is ready for the approver."],
  needs_clarification: ["warn", "Something is missing or contradictory. The recruiter was alerted with the exact fields."],
  blocked_duplicate: ["bad", "Blocked: a case for the same person and start date already exists."],
  needs_sender: ["bad", "The candidate or start date could not be read. The sender must confirm them."],
};

export async function render(root, show) {
  root.append(
    el("h1", {}, "Simulated inbox"),
    el("p", { class: "lead" }, "Synthetic JobDiva start emails. Simulate one arriving in the onboarding mailbox and the Coworker processes it."),
  );
  const result = el("div");
  const list = el("div", { class: "list" });
  root.append(result, el("section", { class: "card" }, el("h2", {}, "Mailbox"), list));

  let messages;
  try {
    messages = await api.inbox();
  } catch (error) {
    list.append(errorNotice(error));
    return;
  }

  for (const message of messages) {
    const button = el("button", { class: "btn primary" }, "Simulate arrival");
    button.addEventListener("click", async () => {
      button.disabled = true;
      result.replaceChildren();
      try {
        const outcome = await api.process(message.id);
        const [tone, text] = OUTCOME[outcome.state] || ["warn", outcome.state];
        const next = outcome.case_id
          ? el("button", { class: "btn", onclick: () => { setCase(outcome.case_id); show(outcome.state === "needs_clarification" ? "chat" : "approval"); } },
              outcome.state === "needs_clarification" ? "Answer in chat" : "Open approval")
          : null;
        result.append(el("div", { class: `notice ${tone}`, role: "status" },
          el("div", { class: "actions" }, statePill(outcome.state), outcome.case_id ? el("span", { class: "mono" }, outcome.case_id) : null),
          el("p", {}, text, outcome.blocked_by ? ` Existing case: ${outcome.blocked_by}.` : ""),
          next));
      } catch (error) {
        result.append(errorNotice(error));
      } finally {
        button.disabled = false;
      }
    });
    list.append(el("div", { class: "row" },
      el("div", {}, el("div", {}, message.subject), el("div", { class: "meta" }, message.from)),
      button));
  }
}
