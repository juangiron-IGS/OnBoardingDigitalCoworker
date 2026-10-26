import { api, el, errorNotice, getCase, setCase, statePill } from "../../shared/api-client.js";

// The conversation lives as long as the page; switching views keeps it.
const conversation = {
  caseId: null,
  messages: [{
    who: "bot",
    text: "Hi! Send me a new start as 'Label: value' lines (at least Candidate ID and Start date), " +
      "or ask how a case is going, for example: How is SYN-0043 doing?",
  }],
};

const SAMPLE_START = `Candidate ID: SYN-0050
Position: QA Engineer
Hiring manager: Lee Example
Start date: 2026-11-23
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
Sponsorship: No`;

export async function render(root, show) {
  root.append(
    el("h1", {}, "Chat"),
    el("p", { class: "lead" },
      "Start a case by chat or ask about one. The Coworker asks one question at a time and only for what is missing or contradictory."),
  );
  const waiting = el("div", { class: "list" });
  const log = el("div", { class: "chat-log", "aria-live": "polite" });
  const context = el("div", { class: "actions" });
  const input = el("textarea", { id: "chat-input", "aria-label": "Message", maxlength: "4000", placeholder: "Type a message…" });
  const send = el("button", { class: "btn primary", type: "submit" }, "Send");
  const sample = el("button", { class: "btn", type: "button", onclick: () => { input.value = SAMPLE_START; input.focus(); } }, "Insert a sample start");
  const fresh = el("button", { class: "btn", type: "button", onclick: () => { conversation.caseId = null; drawContext(context, null); } }, "New conversation");
  const form = el("form", { class: "composer" }, input, el("div", { class: "actions" }, send, sample, fresh));

  root.append(el("div", { class: "grid" },
    el("section", { class: "card" }, el("h2", {}, "Cases waiting for an answer"), waiting),
    el("section", { class: "card chat-panel" }, context, log, form)));

  const redraw = () => {
    log.replaceChildren(...conversation.messages.map((m) => el("div", { class: `bubble${m.who === "me" ? " me" : ""}` },
      el("div", { class: "who" }, m.who === "me" ? "You" : "Coworker"), m.text,
      m.action ? el("div", {}, el("button", { class: "btn", onclick: () => show(m.action.view) }, m.action.label)) : null)));
    log.scrollTop = log.scrollHeight;
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    conversation.messages.push({ who: "me", text });
    input.value = "";
    send.disabled = true;
    redraw();
    try {
      const reply = await api.chat(text, conversation.caseId);
      if (reply.case_id) { conversation.caseId = reply.case_id; setCase(reply.case_id); }
      const action = reply.state === "ready_for_review" ? { view: "approval", label: "Open approval" } : null;
      conversation.messages.push({ who: "bot", text: reply.reply, action });
      drawContext(context, conversation.caseId, reply.state);
      await drawWaiting(waiting, context, redraw);
    } catch (error) {
      log.append(errorNotice(error));
    } finally {
      send.disabled = false;
      redraw();
      input.focus();
    }
  });

  drawContext(context, conversation.caseId);
  redraw();
  await drawWaiting(waiting, context, redraw);
}

function drawContext(root, caseId, stateName) {
  root.replaceChildren(caseId
    ? el("span", { class: "meta" }, "Talking about ", el("span", { class: "mono" }, caseId))
    : el("span", { class: "meta" }, "New conversation"));
  if (stateName) root.append(statePill(stateName));
}

async function drawWaiting(root, context, redraw) {
  let cases;
  try {
    cases = (await api.cases()).filter((c) => c.state === "needs_clarification");
  } catch (error) {
    root.replaceChildren(errorNotice(error));
    return;
  }
  if (!cases.length) {
    root.replaceChildren(el("p", { class: "empty" }, "No case is waiting for an answer."));
    return;
  }
  root.replaceChildren(...cases.map((item) => el("div", {
    class: `row clickable${item.id === conversation.caseId ? " selected" : ""}`,
    tabindex: "0",
    onclick: () => resume(item, context, redraw, root),
    onkeydown: (e) => { if (e.key === "Enter") resume(item, context, redraw, root); },
  }, el("span", { class: "mono" }, item.person_ref), el("span", { class: "meta" }, item.id))));
}

async function resume(item, context, redraw, waiting) {
  conversation.caseId = item.id;
  setCase(item.id);
  const view = await api.case(item.id);
  const next = view.questions[0];
  const ask = next.kind === "missing"
    ? `What is the ${next.label}?`
    : `Two different values were given for ${next.label}. Which one is right?`;
  conversation.messages.push({ who: "bot", text: `Back to ${item.person_ref}. ${ask}` });
  drawContext(context, item.id, view.case.state);
  redraw();
  await drawWaiting(waiting, context, redraw);
}

export { getCase };
