import { api, el, errorNotice, getCase, getRole, setCase, statePill } from "../../shared/api-client.js";

const DECIDABLE = new Set(["ready_for_review", "approval_gate"]);
const FIELD_NAMES = {
  client: "Client", role: "Role", start_date: "Start date", employment_type: "Employment type",
  work_city: "Work city", work_state: "Work state", work_arrangement: "Work arrangement",
  flsa: "FLSA", sponsorship_visa: "Sponsorship / visa", path: "Onboarding path",
  paperwork: "Paperwork", welcome_kit: "Welcome kit", owner: "Owner",
  equipment_request: "Laptop and access request", equipment_overhead: "Equipment overhead", bill_back: "Bill-back",
};

export async function render(root, show) {
  root.append(
    el("h1", {}, "Approval"),
    el("p", { class: "lead" }, "Every line shows its label and its source or rule. Nothing runs on any system until the current version is approved."),
  );
  const picker = el("div", { class: "list" });
  const detail = el("section", { class: "card" });
  root.append(el("section", { class: "card" }, el("h2", {}, "Packages"), picker), detail);

  let cases;
  try {
    cases = (await api.cases()).filter((c) => c.package_version > 0);
  } catch (error) {
    picker.append(errorNotice(error));
    return;
  }
  if (!cases.length) picker.append(el("p", { class: "empty" }, "No package yet. Simulate a complete start email in the inbox."));
  if (!cases.some((c) => c.id === getCase()) && cases.length) setCase(cases[0].id);
  for (const item of cases) {
    picker.append(el("div", {
      class: `row clickable${item.id === getCase() ? " selected" : ""}`,
      tabindex: "0",
      onclick: () => { setCase(item.id); show("approval"); },
      onkeydown: (e) => { if (e.key === "Enter") { setCase(item.id); show("approval"); } },
    }, el("div", {}, el("span", { class: "mono" }, item.person_ref), el("span", { class: "meta" }, ` · v${item.package_version}`)), statePill(item.state)));
  }
  if (getCase() && cases.some((c) => c.id === getCase())) await drawPackage(detail, getCase(), show);
  else detail.append(el("p", { class: "empty" }, "Pick a package to review it."));
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
        setTimeout(() => show("approval"), 1500);
      } catch (error) {
        feedback.replaceChildren(errorNotice(error));
      }
    };
    return el("div", { class: "list" },
      el("div", { class: "actions" }, el("strong", {}, FIELD_NAMES[field]), el("span", { class: `pill ${done ? "ok" : "neutral"}` }, state)),
      canReview ? el("div", { class: "review-edit" }, editor,
        el("div", { class: "actions" },
          el("button", { class: "btn", type: "button", onclick: act("confirm") }, "Confirm recommendation"),
          el("button", { class: "btn primary", type: "button", onclick: act("change") }, "Save change (new version)"))) : null);
  });
  return el("div", {},
    el("h3", {}, "Path and paperwork review"),
    rows,
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
        setTimeout(() => show("approval"), 1500);
      } catch (error) {
        feedback.replaceChildren(errorNotice(error));
      }
    };
    return el("div", { class: "actions" }, el("span", {}, FIELD_NAMES[line.field] || line.field), input,
      el("button", { class: "btn primary", type: "button", onclick: save }, "Record HR's answer"));
  });
  return el("div", {},
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
      setTimeout(() => show("approval"), 1200);
    } catch (error) {
      feedback.replaceChildren(errorNotice(error));
    }
  };
  return el("div", {},
    el("h3", {}, "IT approval of the laptop and access request"),
    el("p", {}, view.case.it_approved ? `IT approved v${pkg.version}.` : `Waiting for IT to approve v${pkg.version}.`),
    getRole() === "it" && !view.case.it_approved
      ? el("div", { class: "actions" }, el("button", { class: "btn primary", onclick: approve }, `Approve request for v${pkg.version}`))
      : null,
    getRole() !== "it" && !view.case.it_approved ? el("p", { class: "lead" }, "Switch to the IT role to approve it.") : null,
    feedback);
}

// US-032: the Coworker recommends the follow-up owner; the supervisor assigns it.
function ownerCard(view, caseId, show) {
  const { recommended_owner: recommended, assigned_owner: assigned } = view.case;
  const input = el("input", { type: "text", "aria-label": "Follow-up owner", maxlength: "120", value: assigned || recommended || "" });
  const feedback = el("div");
  const assign = async () => {
    feedback.replaceChildren();
    try {
      await api.assignOwner(caseId, input.value);
      show("approval");
    } catch (error) {
      feedback.replaceChildren(errorNotice(error));
    }
  };
  const canAssign = getRole() === "approver" && recommended;
  return el("div", {},
    el("h3", {}, "Follow-up owner"),
    el("p", {}, assigned
      ? `Assigned: ${assigned}${assigned === recommended ? " (the recommendation)" : ` (recommended: ${recommended})`}`
      : recommended ? `Recommended, pending assignment: ${recommended}` : "No recommendation yet."),
    canAssign ? el("div", { class: "actions" }, input, el("button", { class: "btn", onclick: assign }, assigned ? "Change owner" : "Assign owner")) : null,
    feedback);
}

async function drawPackage(root, caseId, show) {
  const view = await api.case(caseId);
  const pkg = view.package;
  const lines = [...pkg.lines].sort((a, b) => (a.label === "exception" ? -1 : 0) - (b.label === "exception" ? -1 : 0));
  const exceptions = lines.filter((l) => l.label === "exception");

  root.replaceChildren(...[
    el("div", { class: "actions" }, el("h2", {}, `${view.case.person_ref} · package v${pkg.version}`), statePill(view.case.state),
      el("span", { class: `pill ${pkg.status === "ready" ? "ok" : "bad"}` }, `Package ${pkg.status.replaceAll("_", " ")}`)),
    exceptions.length
      ? el("div", { class: "notice warn" }, `${exceptions.length} open exception${exceptions.length > 1 ? "s" : ""} to review before deciding.`)
      : null,
    el("div", { class: "table-wrap" }, el("table", {},
      el("thead", {}, el("tr", {}, el("th", {}, "Data point"), el("th", {}, "Value"), el("th", {}, "Label"), el("th", {}, "Source or rule"))),
      el("tbody", {}, lines.map((line) => el("tr", {},
        el("td", {}, FIELD_NAMES[line.field] || line.field),
        el("td", {}, line.value ?? "—"),
        el("td", {}, el("span", { class: `pill ${line.label}` }, line.label)),
        el("td", { class: "mono" }, line.source_or_rule_id))))))
  ].filter(Boolean));

  const escalated = exceptions.filter((l) => HR_FIELDS[l.field] && l.source_or_rule_id.includes("JobDiva"));
  if (escalated.length) root.append(hrCard(escalated, caseId, show));
  root.append(ownerCard(view, caseId, show));
  root.append(reviewCard(view, lines, caseId, show));
  if (lines.some((l) => l.field === "equipment_request" && l.label !== "exception")) root.append(itCard(view, pkg, caseId, show));

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
      el("button", { class: "btn primary decision", disabled: !canDecide, onclick: decide("approve") }, `Approve v${pkg.version}`),
      el("button", { class: "btn decision", disabled: !canDecide, onclick: decide("return") }, "Return for correction"),
      el("button", { class: "btn danger decision", disabled: !canDecide, onclick: decide("reject") }, "Reject")),
    getRole() !== "approver" ? el("p", { class: "lead" }, "Only the Approver role can decide. Switch roles at the top right.") : null,
    feedback,
  ].filter(Boolean));
}
