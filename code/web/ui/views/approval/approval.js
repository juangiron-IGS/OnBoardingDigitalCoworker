import { api, caseName, el, errorNotice, getCase, getRole, setCase, statePill } from "../../shared/api-client.js";
import { openChat } from "../../shared/chat-panel.js";
import { igsCard } from "../status/status.js";

const DECIDABLE = new Set(["ready_for_review", "approval_gate"]);
const FIELD_NAMES = {
  client: "Client", role: "Role", start_date: "Start date", employment_type: "Employment type",
  work_city: "Work city", work_state: "Work state", work_arrangement: "Work arrangement",
  flsa: "FLSA", sponsorship_visa: "Sponsorship / visa", path: "Onboarding path",
  paperwork: "Paperwork", welcome_kit: "Welcome kit", owner: "Owner",
  equipment_request: "Laptop and access request", equipment_overhead: "Equipment overhead", bill_back: "Bill-back",
};

// Each role sees only the package lines it approves or adjusts; the approver sees all.
const ROLE_FIELDS = {
  it: ["equipment_request", "equipment_overhead", "bill_back"],
  onboarding: ["path", "paperwork", "welcome_kit", "owner"],
  ldc: ["welcome_kit"],
};
const LEADS = {
  recruiter: "What you sent in the start email, and what you still need to complete.",
  it: "The laptop, access and equipment lines IT approves.",
  onboarding: "The open exceptions and the path and paperwork the Onboarding Team reviews.",
  ldc: "The new hires in the LDC tracker: approve the welcome kit and the leader messages.",
  approver: "Every line shows its label and its source or rule. Nothing runs on any system until the current version is approved.",
};

// Whether the open case was closed with a second click.
let collapsed = false;

export async function render(root, show) {
  const recruiter = getRole() === "recruiter";
  root.append(
    el("h1", {}, "Approval"),
    el("p", { class: "lead" }, LEADS[getRole()] || LEADS.approver),
  );
  const picker = el("div", { class: "list" });
  const detail = el("section", { class: "card" });
  root.append(el("section", { class: "card" }, el("h2", {}, "Packages"), picker), detail);

  let cases;
  try {
    // The recruiter also sees the cases still waiting for their answers.
    cases = (await api.cases()).filter((c) => c.package_version > 0 || (recruiter && c.state === "needs_clarification"));
  } catch (error) {
    picker.append(errorNotice(error));
    return;
  }
  if (!recruiter) {
    const views = await Promise.all(cases.map((c) => api.case(c.id).catch(() => null)));
    cases = cases.filter((c, i) => views[i] && pendingFor(getRole(), views[i]));
  }
  if (!cases.length) picker.append(el("p", { class: "empty" }, recruiter
    ? "No package yet. Simulate a complete start email in the inbox."
    : "Nothing pending for your role. Completed steps are on the Dashboard."));
  if (!collapsed && !cases.some((c) => c.id === getCase()) && cases.length) setCase(cases[0].id);
  // A click opens a case under its row; a second click on it closes it.
  const toggle = (id) => { collapsed = id === getCase() && !collapsed; setCase(id); show("approval"); };
  for (const item of cases) {
    const isOpen = !collapsed && item.id === getCase();
    picker.append(el("div", {
      class: `row clickable${isOpen ? " selected" : ""}`,
      tabindex: "0",
      "aria-expanded": String(isOpen),
      onclick: () => toggle(item.id),
      onkeydown: (e) => { if (e.key === "Enter") toggle(item.id); },
    }, el("div", {}, el("div", {}, el("span", { class: "chevron", "aria-hidden": "true" }, isOpen ? "▾ " : "▸ "), el("span", { class: "mono" }, item.person_ref), el("span", { class: "meta" }, item.package_version ? ` · v${item.package_version}` : " · waiting for your answers")),
      el("div", { class: "meta" }, caseName(item))), statePill(item.state)));
  }
  // The selected case opens like an accordion, right under its row.
  const open = picker.querySelector(".row.selected");
  if (open) {
    open.after(detail);
    await (recruiter ? drawRecruiter : drawPackage)(detail, getCase(), show);
    open.scrollIntoView({ block: "start" });
  } else detail.append(el("p", { class: "empty" }, "Pick a package to review it."));
}

// Whether this role still has to approve or adjust something on the case.
function pendingFor(role, view) {
  const { case: c, package: pkg } = view;
  const lines = pkg?.lines || [];
  if (role === "onboarding") {
    const review = c.data.team_review || {};
    const toHr = lines.some((l) => l.label === "exception" && HR_FIELDS[l.field] && l.source_or_rule_id.includes("JobDiva"));
    return c.state === "ready_for_review" && (!review.path || !review.paperwork || toHr);
  }
  if (role === "it") return !c.it_approved && lines.some((l) => l.field === "equipment_request" && l.label !== "exception") && DECIDABLE.has(c.state);
  if (role === "approver") return DECIDABLE.has(c.state) || Boolean(c.recommended_owner && !c.assigned_owner);
  if (role === "ldc") return ldcPending(view);
  return true;
}

// US-028, US-029: after approval the case is in the LDC tracker; LDC approves the
// welcome kit and then the leader messages.
function ldcPending(view) {
  if (!view.records.some((r) => r.system === "ldc_tracker")) return false;
  const shipped = view.records.some((r) => r.system === "welcome_kits");
  const documentsOpen = ["documents_pending", "in_verification"].includes(view.case.state);
  const messages = view.leader_messages || [];
  return (!shipped && !documentsOpen) || (shipped && !messages.length) || messages.some((m) => m.status === "draft");
}

// US-007 AC-003: a cited rule opens to show its owner, version and status.
const RULE_ID = /^R-[A-Z]+-\d+$/;

function ruleCell(sourceOrRule) {
  if (!RULE_ID.test(sourceOrRule)) return sourceOrRule;
  const detail = el("div", { class: "meta" });
  const open = async () => {
    if (detail.textContent) { detail.replaceChildren(); return; }
    try {
      const rule = await api.rule(sourceOrRule);
      const when = Object.entries(rule.when).map(([k, v]) => `${k}: ${v}`).join(", ") || "every case";
      detail.replaceChildren(`Owner: ${rule.owner} · version ${rule.version} · ${rule.status} · applies when ${when}`);
    } catch (error) {
      detail.replaceChildren(errorNotice(error));
    }
  };
  return el("div", {}, el("button", { class: "link", type: "button", title: "Show the rule", onclick: open }, sourceOrRule), detail);
}

// US-026: the Onboarding Team confirms or changes the recommended path and paperwork.
function reviewCard(view, lines, caseId, show) {
  const review = view.case.data.team_review || {};
  const feedback = el("div");
  const canReview = getRole() === "onboarding" && view.case.state === "ready_for_review";
  const rows = ["path", "paperwork"].map((field) => {
    const current = lines.filter((l) => l.field === field).map((l) => l.value);
    const done = review[field];
    const state = done
      ? (done.confirmed ? `Confirmed by the Onboarding Team (v${done.version})` : `Changed by the Onboarding Team (from v${done.version})`)
      : "Recommended, not reviewed yet";
    const editor = el("textarea", { rows: "3", maxlength: "4000", "aria-label": `New ${FIELD_NAMES[field]}, one per line` }, current.join(String.fromCharCode(10)));
    const act = (action) => async () => {
      feedback.replaceChildren();
      try {
        const values = action === "change" ? editor.value.split(/\r?\n/).map((v) => v.trim()).filter(Boolean) : [];
        const outcome = await api.review(caseId, field, action, values);
        feedback.replaceChildren(el("div", { class: "notice ok", role: "status" },
          action === "confirm" ? `${FIELD_NAMES[field]} confirmed.` : `${FIELD_NAMES[field]} changed. Package v${outcome.package_version} is ready for the approver.`));
        setTimeout(show, 800);
      } catch (error) {
        feedback.replaceChildren(errorNotice(error));
      }
    };
    return el("div", { class: "list", "data-pending": canReview && !done },
      el("div", { class: "actions" }, el("strong", {}, FIELD_NAMES[field]), el("span", { class: `pill ${done ? "ok" : "neutral"}` }, state)),
      done ? el("p", { class: "meta" }, current.join(" · ")) : null,
      canReview && !done ? el("div", { class: "review-edit" }, editor,
        el("div", { class: "actions" },
          el("button", { class: "btn", type: "button", onclick: act("confirm") }, "Confirm recommendation"),
          el("button", { class: "btn primary", type: "button", onclick: act("change") }, "Save change (new version)"))) : null);
  });
  const reviewed = canReview && ["path", "paperwork"].every((field) => review[field]);
  return el("div", {},
    el("h3", {}, "Path and paperwork review"),
    rows,
    reviewed ? el("div", { class: "notice ok", "data-done": true }, "Path and paperwork reviewed. The package is with the approver.") : null,
    getRole() !== "onboarding" ? el("p", { class: "lead" }, "The Onboarding Team confirms or changes these. Switch to that role to review.") : null,
    feedback);
}

// US-027: HR decides FLSA and classification; the Onboarding Team records the answer.
const HR_FIELDS = { flsa: ["Exempt", "Non-exempt"], employment_type: ["W-2", "Contractor", "Corp-to-corp"] };

function hrCard(lines, caseId, show) {
  const feedback = el("div");
  const forms = lines.map((line) => {
    const choices = HR_FIELDS[line.field];
    const input = choices
      ? el("select", { "aria-label": `HR's answer for ${FIELD_NAMES[line.field]}` }, choices.map((c) => el("option", { value: c }, c)))
      : el("input", { type: "text", maxlength: "60", "aria-label": `HR's answer for ${FIELD_NAMES[line.field]}` });
    const save = async () => {
      feedback.replaceChildren();
      try {
        const outcome = await api.hrAnswer(caseId, line.field, input.value);
        feedback.replaceChildren(el("div", { class: "notice ok", role: "status" },
          `HR's answer recorded. Package v${outcome.package_version} was rebuilt and is ready for the approver.`));
        setTimeout(show, 800);
      } catch (error) {
        feedback.replaceChildren(errorNotice(error));
      }
    };
    return el("div", { class: "actions" }, el("span", {}, FIELD_NAMES[line.field] || line.field), input,
      el("button", { class: "btn primary", type: "button", onclick: save }, "Record HR's answer"));
  });
  return el("div", { "data-pending": getRole() === "onboarding" },
    el("h3", {}, "Escalated to HR"),
    el("p", { class: "lead" }, "The Coworker does not decide FLSA or classification. Record HR's decision to rebuild the package."),
    getRole() === "onboarding" ? forms : el("p", { class: "lead" }, "Switch to the Onboarding Team role to record HR's answer."),
    feedback);
}

// US-020 AC-002: the laptop request goes to Chelsea Tech only after IT and the approver approve.
function itCard(view, pkg, caseId, show) {
  const feedback = el("div");
  const approve = async () => {
    feedback.replaceChildren();
    try {
      const outcome = await api.approveIt(caseId, pkg.version);
      feedback.replaceChildren(el("div", { class: "notice ok", role: "status" },
        outcome.sent ? "IT approved. The request was sent to Chelsea Tech (simulated)." : "IT approved. The request is sent once the approver approves this version."));
      setTimeout(show, 800);
    } catch (error) {
      feedback.replaceChildren(errorNotice(error));
    }
  };
  return el("div", { "data-pending": getRole() === "it" && !view.case.it_approved },
    el("h3", {}, "IT approval of the laptop and access request"),
    el("p", {}, view.case.it_approved ? `IT approved v${pkg.version}.` : `Waiting for IT to approve v${pkg.version}. The request goes to Chelsea Tech once IT and the package are both approved.`),
    getRole() === "it" && !view.case.it_approved
      ? el("div", { class: "actions" }, el("button", { class: "btn primary", onclick: approve }, `Approve request for v${pkg.version}`))
      : null,
    getRole() !== "it" && !view.case.it_approved ? el("p", { class: "lead" }, "Switch to the IT role to approve it.") : null,
    feedback);
}

// US-032: the Coworker recommends the follow-up owner; the supervisor assigns it
// to the recommendation or to a person of the Onboarding Team.
function ownerCard(view, caseId, show, team) {
  const { recommended_owner: recommended, assigned_owner: assigned } = view.case;
  const names = [...new Set([recommended, ...team, assigned].filter(Boolean))];
  const input = el("select", { "aria-label": "Follow-up owner" },
    names.map((name) => el("option", { value: name, selected: name === (assigned || recommended) },
      name === recommended ? `${name} (recommended)` : name)));
  const feedback = el("div");
  const assign = async () => {
    feedback.replaceChildren();
    try {
      await api.assignOwner(caseId, input.value);
      show();
    } catch (error) {
      feedback.replaceChildren(errorNotice(error));
    }
  };
  const canAssign = getRole() === "approver" && recommended;
  return el("div", { "data-pending": canAssign && !assigned },
    el("h3", {}, "Follow-up owner"),
    el("p", {}, assigned
      ? `Assigned: ${assigned}${assigned === recommended ? " (the recommendation)" : ` (recommended: ${recommended})`}`
      : recommended ? `Recommended, pending assignment: ${recommended}` : "No recommendation yet."),
    canAssign ? el("div", { class: "actions" }, input, el("button", { class: "btn primary", onclick: assign }, assigned ? "Change owner" : "Assign owner")) : null,
    feedback);
}

// Opens the chat on the case: a panel on the web app, the Chat tab in the desktop window.
function completeInChat(caseId, show) {
  if (document.body.classList.contains("desktop")) show(`chat/${encodeURIComponent(caseId)}`);
  else openChat(caseId);
}

function linesTable(lines) {
  return el("div", { class: "table-wrap" }, el("table", {},
    el("thead", {}, el("tr", {}, el("th", {}, "Data point"), el("th", {}, "Value"), el("th", {}, "Label"), el("th", {}, "Source or rule"))),
    el("tbody", {}, lines.map((line) => el("tr", {},
      el("td", {}, FIELD_NAMES[line.field] || line.field),
      el("td", {}, line.value ?? "—"),
      el("td", {}, el("span", { class: `pill ${line.label}` }, line.label)),
      el("td", { class: "mono" }, ruleCell(line.source_or_rule_id)))))));
}

// US-004: the recruiter sees the data they sent and the fields still to complete.
async function drawRecruiter(root, caseId, show) {
  const view = await api.case(caseId);
  const sent = (view.package?.lines || []).filter((l) => l.source_or_rule_id === "email" && String(l.value ?? "").trim());
  const missing = view.questions || [];
  root.replaceChildren(...[
    el("div", { class: "actions" }, el("h2", {}, view.case.person_ref), el("span", { class: "meta" }, caseName(view.case.data)), statePill(view.case.state)),
    missing.length
      ? el("div", { class: "notice warn" },
          el("div", {}, `To complete: ${missing.map((q) => q.label).join(", ")}.`),
          el("div", { class: "actions" }, el("button", { class: "btn primary", type: "button", onclick: () => completeInChat(caseId, show) }, "Complete in the chat")))
      : el("div", { class: "notice ok" }, "Nothing to complete. The package is with the Onboarding Team and the approver."),
    el("h3", {}, "What you sent"),
    sent.length ? linesTable(sent) : el("p", { class: "empty" }, "The package is built once the start data is complete."),
  ]);
}

// After an action, show the same case at its next pending step, not the top of the view.
function goToNextStep(root) {
  const next = root.querySelector("[data-pending]") || root.querySelector(".decision:not([disabled])") || root.querySelector("[data-done]");
  if (!next) return;
  next.scrollIntoView({ block: "center", behavior: "smooth" });
  next.querySelector("button, textarea, select")?.focus({ preventScroll: true });
}

async function drawPackage(root, caseId, show) {
  const refresh = async () => { await drawPackage(root, caseId, show); goToNextStep(root); };
  const role = getRole();
  const view = await api.case(caseId);
  const pkg = view.package;
  const fields = ROLE_FIELDS[role];
  const lines = [...pkg.lines].filter((l) => !fields || fields.includes(l.field) || (role === "onboarding" && l.label === "exception")).sort((a, b) => (a.label === "exception" ? -1 : 0) - (b.label === "exception" ? -1 : 0));
  const exceptions = lines.filter((l) => l.label === "exception");

  root.replaceChildren(...[
    el("div", { class: "actions" }, el("h2", {}, `${view.case.person_ref} · package v${pkg.version}`), el("span", { class: "meta" }, caseName(view.case.data)), statePill(view.case.state),
      el("span", { class: `pill ${pkg.status === "ready" ? "ok" : "bad"}` }, `Package ${pkg.status.replaceAll("_", " ")}`)),
    exceptions.length
      ? el("div", { class: "notice warn" }, `${exceptions.length} open exception${exceptions.length > 1 ? "s" : ""} to review before deciding.`)
      : null,
    lines.length ? linesTable(lines) : el("p", { class: "empty" }, "Nothing in this package for your role."),
  ].filter(Boolean));

  const escalated = exceptions.filter((l) => HR_FIELDS[l.field] && l.source_or_rule_id.includes("JobDiva"));
  if (escalated.length && role === "onboarding") root.append(hrCard(escalated, caseId, refresh));
  if (role === "approver") root.append(ownerCard(view, caseId, refresh, (await api.team().catch(() => ({ members: [] }))).members));
  if (role === "onboarding") root.append(reviewCard(view, lines, caseId, refresh));
  // The approver sees IT's step only while it is still open; once IT approved,
  // the package approval is all that is left.
  if ((role === "it" || (role === "approver" && !view.case.it_approved)) && lines.some((l) => l.field === "equipment_request" && l.label !== "exception")) root.append(itCard(view, pkg, caseId, refresh));
  if (role === "ldc" && view.records.some((r) => r.system === "ldc_tracker")) root.append(igsCard(view, caseId, refresh));
  if (role !== "approver") return;

  const feedback = el("div");
  const canDecide = getRole() === "approver" && DECIDABLE.has(view.case.state) && pkg.status === "ready";
  const decide = (decision) => async () => {
    feedback.replaceChildren();
    try {
      const outcome = await api.decide(caseId, pkg.version, decision);
      const text = decision === "approve"
        ? `Approved with ${outcome.approval_id}. The JobDiva and Workflow agent created ${outcome.actions.length} simulated records.`
        : decision === "return" ? "Returned for correction. The case goes back to Validated and will need a new approval."
        : "Rejected. The case stops here.";
      feedback.replaceChildren(el("div", { class: "notice ok", role: "status" }, text,
        el("div", {}, el("button", { class: "btn", onclick: () => show("status") }, "See status and audit"))));
      root.querySelectorAll(".decision").forEach((b) => { b.disabled = true; });
    } catch (error) {
      feedback.replaceChildren(errorNotice(error));
    }
  };
  root.append(...[
    el("div", { class: "actions" },
      el("button", { class: "btn primary decision", disabled: !canDecide, onclick: decide("approve") }, `Approve package v${pkg.version}`),
      el("button", { class: "btn decision", disabled: !canDecide, onclick: decide("return") }, "Return for correction"),
      el("button", { class: "btn danger decision", disabled: !canDecide, onclick: decide("reject") }, "Reject")),
    feedback,
  ].filter(Boolean));
}
