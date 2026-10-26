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

  root.append(ownerCard(view, caseId, show));
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
