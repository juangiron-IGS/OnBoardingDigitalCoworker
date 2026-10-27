import { api, el, errorNotice, getRole } from "../../shared/api-client.js";

// US-025: the Onboarding Knowledge agent answers from records the Onboarding Team validates.
const STATUS = {
  validated: ["ok", "Validated"],
  unvalidated: ["warn", "Unvalidated draft"],
  rejected: ["bad", "Rejected"],
};
const REASON = { no_answer: "No record answers it", hr_decision: "For HR (FLSA, classification or legal)" };

export async function render(root, show) {
  root.append(
    el("h1", {}, "Onboarding knowledge"),
    el("p", { class: "lead" }, "Ask a process question. Answers cite their record; drafts are labelled until the Onboarding Team validates them, and unanswered questions stay pending for the team."),
  );

  const input = el("input", { class: "wide", type: "text", maxlength: "1000", "aria-label": "Your question", placeholder: "Which forms does a W-2 hire in Texas need?" });
  const result = el("div");
  const ask = async () => {
    result.replaceChildren();
    if (!input.value.trim()) return;
    try {
      const answer = await api.askKnowledge(input.value.trim());
      const tone = { validated: "ok", unvalidated: "warn" }[answer.status] || "neutral";
      result.replaceChildren(el("div", { class: `notice ${tone === "neutral" ? "" : tone}`, role: "status" }, answer.reply));
      if (answer.pending_id) setTimeout(() => show("knowledge"), 2500);
    } catch (error) {
      result.replaceChildren(errorNotice(error));
    }
  };
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") ask(); });
  root.append(el("section", { class: "card" },
    el("h2", {}, "Ask"),
    el("div", { class: "actions" }, input, el("button", { class: "btn primary", type: "button", onclick: ask }, "Ask")),
    result));

  const records = el("div", { class: "list" });
  const pending = el("div", { class: "list" });
  root.append(el("div", { class: "grid" },
    el("section", { class: "card" }, el("h2", {}, "Knowledge records"), records),
    el("section", { class: "card" }, el("h2", {}, "Pending for the Onboarding Team"), pending)));

  let view;
  try {
    view = await api.knowledge();
  } catch (error) {
    records.append(errorNotice(error));
    return;
  }

  const canValidate = getRole() === "onboarding";
  for (const record of view.records) {
    const [tone, label] = STATUS[record.status];
    const decide = (decision) => async () => {
      try {
        await api.validateKnowledge(record.id, decision);
        show("knowledge");
      } catch (error) {
        records.prepend(errorNotice(error));
      }
    };
    records.append(el("div", { class: "row" },
      el("div", {},
        el("div", {}, el("span", { class: "mono" }, record.id), ` · ${record.title}`),
        el("div", { class: "meta" }, `${record.question} · ${record.source}`)),
      el("div", { class: "actions" },
        el("span", { class: `pill ${tone}` }, label),
        canValidate && record.status !== "validated" ? el("button", { class: "btn", type: "button", onclick: decide("validated") }, "Validate") : null,
        canValidate && record.status === "unvalidated" ? el("button", { class: "btn danger", type: "button", onclick: decide("rejected") }, "Reject") : null)));
  }
  if (!canValidate) records.append(el("p", { class: "lead" }, "Only the Onboarding Team validates or rejects records. Switch to that role to do it."));

  if (!view.pending.length) pending.append(el("p", { class: "empty" }, "No pending questions."));
  for (const question of view.pending) {
    pending.append(el("div", { class: "row" },
      el("div", {}, el("div", {}, question.question),
        el("div", { class: "meta" }, `${question.id} · asked by ${question.asked_by} via ${question.channel} · ${REASON[question.reason] || question.reason}`)),
      el("span", { class: "meta" }, new Date(question.asked_at).toLocaleTimeString())));
  }
}
