import { api, el, errorNotice, getCase, setCase, statePill } from "../../shared/api-client.js";

export async function render(root, show) {
  root.append(
    el("h1", {}, "Chat"),
    el("p", { class: "lead" }, "The Coworker asks only for what is missing or contradictory, naming the exact field. Answer each question once."),
  );
  const picker = el("div", { class: "list" });
  const conversation = el("section", { class: "card chat" });
  root.append(el("div", { class: "grid" }, el("section", { class: "card" }, el("h2", {}, "Cases waiting for an answer"), picker), conversation));

  let cases;
  try {
    cases = (await api.cases()).filter((c) => c.state === "needs_clarification");
  } catch (error) {
    picker.append(errorNotice(error));
    return;
  }
  if (!cases.length) picker.append(el("p", { class: "empty" }, "No case is waiting for an answer. Simulate the “QA Engineer” email in the inbox."));
  if (!cases.some((c) => c.id === getCase()) && cases.length) setCase(cases[0].id);

  for (const item of cases) {
    picker.append(el("div", {
      class: `row clickable${item.id === getCase() ? " selected" : ""}`,
      tabindex: "0",
      onclick: () => { setCase(item.id); show("chat"); },
      onkeydown: (e) => { if (e.key === "Enter") { setCase(item.id); show("chat"); } },
    }, el("span", { class: "mono" }, item.person_ref), el("span", { class: "meta" }, item.id)));
  }
  if (getCase() && cases.some((c) => c.id === getCase())) await drawConversation(conversation, getCase(), show);
  else conversation.append(el("p", { class: "empty" }, "Pick a case to see its questions."));
}

async function drawConversation(root, caseId, show) {
  const view = await api.case(caseId);
  root.replaceChildren(
    el("div", { class: "actions" }, el("strong", {}, view.case.person_ref), statePill(view.case.state)),
  );
  if (!view.questions.length) {
    root.append(el("div", { class: "bubble" }, "Thanks, the case is complete."),
      el("button", { class: "btn primary", onclick: () => show("approval") }, "Open approval"));
    return;
  }
  const missing = view.questions.filter((q) => q.kind === "missing").map((q) => q.label);
  const contradictions = view.questions.filter((q) => q.kind === "contradiction").map((q) => q.label);
  root.append(el("div", { class: "bubble" },
    "Coworker: ",
    missing.length ? `I still need ${missing.join(" and ")}. ` : "",
    contradictions.length ? `Two different values were given for ${contradictions.join(", ")}; please confirm one.` : ""));

  const feedback = el("div");
  for (const question of view.questions) {
    const id = `answer-${question.field}`;
    const input = el("input", { id, required: true, maxlength: "500", autocomplete: "off" });
    const send = el("button", { class: "btn primary" }, "Send");
    const form = el("form", { class: "answer" }, el("label", { for: id }, question.label), input, send);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!input.value.trim()) return;
      send.disabled = true;
      try {
        const result = await api.answer(caseId, question.field, input.value.trim());
        root.append(el("div", { class: "bubble me" }, `${question.label}: ${input.value.trim()}`));
        if (result.state === "ready_for_review") {
          root.append(el("div", { class: "bubble" }, "Coworker: thanks. The case is complete and the package is ready for approval."),
            el("button", { class: "btn primary", onclick: () => show("approval") }, "Open approval"));
          form.remove();
        } else {
          form.remove();
        }
      } catch (error) {
        feedback.replaceChildren(errorNotice(error));
        send.disabled = false;
      }
    });
    root.append(form);
  }
  root.append(feedback);
}
