import { api, el, errorNotice, getCase, getRole, setCase, statePill, STATE_LABELS } from "../../shared/api-client.js";

const PATH = ["received", "validated", "case_set_up", "ready_for_review", "approval_gate", "approved", "actions_executed",
  "documents_pending", "in_verification", "sent_to_payroll"];
const SYSTEMS = { jobdiva_cases: "JobDiva case (mock)", task_lists: "Onboarding task list", it_requests: "IT request (mock)",
  payroll_packages: "Payroll package (Paychex mock)", ldc_tracker: "LDC tracker entry (SharePoint mock)",
  welcome_kits: "Welcome kit shipment (mock)" };
const MESSAGE_KIND = { feedback_request: "Leader feedback request", congratulation: "Congratulation" };
const DOC_STATUS = { outstanding: ["warn", "Outstanding"], pending_countersign: ["neutral", "Pending countersign"], verified: ["ok", "Verified"] };

export async function render(root, show) {
  root.append(
    el("h1", {}, "Status"),
    el("p", { class: "lead" }, "Where each case is, every action the agents took, and the records created in the simulated systems."),
  );
  const picker = el("div", { class: "list" });
  const detail = el("div", { class: "list" });
  root.append(el("section", { class: "card" }, el("h2", {}, "Cases"), picker), detail);

  let cases;
  try {
    cases = await api.cases();
  } catch (error) {
    picker.append(errorNotice(error));
    return;
  }
  if (!cases.length) picker.append(el("p", { class: "empty" }, "No cases yet. Start one from the simulated inbox."));
  if (!cases.some((c) => c.id === getCase()) && cases.length) setCase(cases[0].id);
  for (const item of cases) {
    picker.append(el("div", {
      class: `row clickable${item.id === getCase() ? " selected" : ""}`,
      tabindex: "0",
      onclick: () => { setCase(item.id); show("status"); },
      onkeydown: (e) => { if (e.key === "Enter") { setCase(item.id); show("status"); } },
    }, el("div", {}, el("span", { class: "mono" }, item.person_ref), el("span", { class: "meta" }, ` · starts ${item.start_date}`)), statePill(item.state)));
  }
  if (getCase()) await drawCase(detail, getCase(), show);
}

// US-012: package ready within 5 minutes of the last answer, or reported as late.
function timingLine(timing) {
  if (!timing) return null;
  return el("p", {}, `Package ready ${timing.seconds} s after the last answer `,
    el("span", { class: `pill ${timing.met ? "ok" : "bad"}` }, timing.met ? "Within the 5-minute target" : "Missed the 5-minute target"));
}

// US-022..024: checklist and reminders, countersign, payroll handoff and returns.
function followupCard(view, caseId, show) {
  if (!view.checklist.length) return null;
  const feedback = el("div");
  const isTeam = getRole() === "onboarding";
  const state = view.case.state;
  const act = (work, message) => async () => {
    feedback.replaceChildren();
    try {
      const result = await work();
      feedback.replaceChildren(el("div", { class: "notice ok", role: "status" }, message(result)));
      setTimeout(() => show("status"), 1200);
    } catch (error) {
      feedback.replaceChildren(errorNotice(error));
    }
  };
  const lastHour = Math.max(0, ...view.reminders.map((r) => r.at_hours));
  const nextHour = lastHour + 24;
  const rows = view.checklist.map((c) => {
    const [tone, label] = DOC_STATUS[c.status];
    return el("div", { class: "row" },
      el("div", {}, el("div", {}, c.item), el("div", { class: "meta mono" }, c.required_by)),
      el("div", { class: "actions" },
        el("span", { class: `pill ${tone}` }, label),
        isTeam && c.status === "outstanding" ? el("button", { class: "btn", type: "button",
          onclick: act(() => api.deliver(caseId, [c.item]), (r) => r.missing.length ? `Still missing: ${r.missing.join("; ")}.` : "Everything delivered. The case moves to In verification.") }, "Candidate delivered") : null,
        isTeam && c.status === "pending_countersign" ? el("button", { class: "btn primary", type: "button",
          onclick: act(() => api.countersign(caseId, c.item), () => `${c.item} verified.`) }, "Countersign") : null));
  });
  const allVerified = view.checklist.every((c) => c.status === "verified");
  const outstanding = view.checklist.filter((c) => c.status === "outstanding").map((c) => c.item);
  const mail = view.candidate_email;
  return el("section", { class: "card" },
    el("h2", {}, "Candidate documents"),
    mail ? el("details", { class: "email-preview", open: state === "documents_pending" },
      el("summary", {}, "Email sent to the candidate (simulated)"),
      el("div", { class: "meta" }, `To: ${mail.to}`),
      el("div", {}, el("strong", {}, mail.subject)),
      mail.body.map((line) => el("p", {}, line))) : null,
    isTeam && state === "documents_pending" && outstanding.length ? el("div", { class: "actions" },
      el("button", { class: "btn primary", type: "button",
        onclick: act(() => api.deliver(caseId, outstanding), (r) => r.missing.length ? `Still missing: ${r.missing.join("; ")}.` : "The candidate sent every document. Countersign each one to verify it.") },
        "Simulate: the candidate sent the documents")) : null,
    el("p", { class: "lead" }, "The checklist the candidate received. A delivered document is verified only when the Onboarding Team countersigns it."),
    el("div", { class: "list" }, rows),
    el("h3", {}, "Reminders"),
    view.reminders.length
      ? el("div", { class: "list" }, view.reminders.map((r) => el("div", { class: "row" },
          el("div", {}, r.kind === "reminder" ? `Reminder to the candidate at ${r.at_hours} h` : `Escalated to the Onboarding Team at ${r.at_hours} h`),
          el("span", { class: "meta mono" }, r.rule_id))))
      : el("p", { class: "empty" }, "No reminders yet."),
    isTeam && state === "documents_pending" ? el("div", { class: "actions" },
      el("button", { class: "btn", type: "button", onclick: act(() => api.runFollowup(caseId, nextHour),
        (r) => r.sent.length ? `At ${nextHour} h: ${r.sent.map((s) => s.kind).join(" and ")} sent.` : `At ${nextHour} h: nothing due.`) },
        `Simulate time: ${nextHour} h after the checklist`)) : null,
    el("h3", {}, "Payroll"),
    state === "in_verification" && isTeam
      ? el("div", { class: "actions" }, el("button", { class: "btn primary", type: "button", disabled: !allVerified,
          onclick: act(() => api.payrollHandoff(caseId, view.case.package_version), () => "Handoff approved. The payroll package was sent to Paychex (simulated).") },
          "Approve payroll handoff"),
          allVerified ? null : el("span", { class: "meta" }, "Every document must be verified first."))
      : null,
    state === "sent_to_payroll" ? el("div", {},
      el("p", {}, "The payroll package was sent with validated data only."),
      view.payroll_returns.length
        ? el("div", { class: "list" }, view.payroll_returns.map((t) => el("div", { class: "row" },
            el("div", {}, el("div", {}, `Task: ${t.issue}`), el("div", { class: "meta" }, "Returned by Payroll")),
            el("span", { class: "meta" }, new Date(t.received_at).toLocaleTimeString()))))
        : null,
      isTeam ? el("button", { class: "btn", type: "button",
        onclick: act(() => api.payrollReturn(caseId, "Bank account number does not match the direct deposit form"), () => "Payroll return recorded as a task.") },
        "Simulate a Paychex return") : null) : null,
    !isTeam ? el("p", { class: "lead" }, "Switch to the Onboarding Team role to record deliveries, countersign and approve the payroll handoff.") : null,
    feedback);
}

// US-031: information package from validated knowledge, sent after the team reviews it.
function infoPackageCard(view, caseId, show) {
  if (!["approved", "actions_executed", "documents_pending", "in_verification", "sent_to_payroll"].includes(view.case.state)) return null;
  const isTeam = getRole() === "onboarding";
  const feedback = el("div");
  const act = (work, message) => async () => {
    feedback.replaceChildren();
    try {
      await work();
      feedback.replaceChildren(el("div", { class: "notice ok", role: "status" }, message));
      setTimeout(() => show("status"), 1200);
    } catch (error) {
      feedback.replaceChildren(errorNotice(error));
    }
  };
  const pkg = view.info_package;
  return el("section", { class: "card" },
    el("h2", {}, "New-hire information package"),
    el("p", { class: "lead" }, "Company, client and role information from validated knowledge only. It goes to the new hire after the Onboarding Team reviews it."),
    pkg ? el("div", { class: "list" },
      pkg.content.sections.length ? pkg.content.sections.map((s) => el("div", { class: "row" },
        el("div", {}, el("div", {}, `${s.heading} · ${s.title}`), el("div", { class: "meta" }, s.text)),
        el("span", { class: "meta mono" }, s.record_id)))
        : el("p", { class: "empty" }, "No validated information for this company, client or role yet."),
      el("span", { class: `pill ${pkg.status === "sent" ? "ok" : "warn"}` }, pkg.status === "sent" ? "Reviewed and sent" : "Waiting for the team's review"))
      : null,
    isTeam && !pkg ? el("button", { class: "btn", type: "button", onclick: act(() => api.prepareInfoPackage(caseId), "Package prepared for your review.") }, "Prepare the package") : null,
    isTeam && pkg && pkg.status === "draft" ? el("button", { class: "btn primary", type: "button", onclick: act(() => api.sendInfoPackage(caseId), "Sent to the new hire.") }, "Reviewed: send to the new hire") : null,
    feedback);
}

// US-028, US-029: LDC tracker, welcome kit and leader messages, all approved by LDC.
export function igsCard(view, caseId, show) {
  const entry = view.records.find((r) => r.system === "ldc_tracker");
  if (!entry) return null;
  const shipped = view.records.some((r) => r.system === "welcome_kits");
  const isLdc = getRole() === "ldc";
  const feedback = el("div");
  const act = (work, message) => async () => {
    feedback.replaceChildren();
    try {
      const result = await work();
      feedback.replaceChildren(el("div", { class: "notice ok", role: "status" }, message(result)));
      setTimeout(() => show("status"), 1200);
    } catch (error) {
      feedback.replaceChildren(errorNotice(error));
    }
  };
  const messages = view.leader_messages || [];
  return el("section", { class: "card" },
    el("h2", {}, "Culture and Belonging (IGS)"),
    el("p", {}, `In the LDC tracker. Welcome kit: ${entry.data.welcome_kit}, to ship by ${entry.data.kit_ship_by}. Leader feedback due ${entry.data.feedback_due}.`),
    el("div", { class: "actions" },
      el("span", { class: `pill ${shipped ? "ok" : "warn"}` }, shipped ? "Kit approved by LDC and shipped" : "Kit waiting for LDC approval"),
      isLdc && !shipped ? el("button", { class: "btn primary", type: "button",
        onclick: act(() => api.approveKit(caseId, view.case.package_version), () => "Kit approved. The shipment was sent (simulated).") }, "Approve welcome kit") : null,
      isLdc && !messages.length ? el("button", { class: "btn", type: "button",
        onclick: act(() => api.runIgs(caseId, 60), (r) => r.drafted.length ? "Two months reached: the leader messages are drafted for your approval." : "Nothing to draft yet.") },
        "Simulate two months after the start") : null),
    messages.length ? el("div", { class: "list" }, messages.map((m) => el("div", { class: "row" },
      el("div", {}, el("div", {}, `${MESSAGE_KIND[m.kind] || m.kind} to ${m.recipient}`), el("div", { class: "meta" }, m.text)),
      el("div", { class: "actions" },
        el("span", { class: `pill ${m.status === "sent" ? "ok" : "warn"}` }, m.status === "sent" ? "Sent" : "Waiting for LDC"),
        isLdc && m.status === "draft" ? el("button", { class: "btn", type: "button",
          onclick: act(() => api.approveLeaderMessage(caseId, m.id), () => "Approved and sent.") }, "Approve and send") : null)))) : null,
    !isLdc ? el("p", { class: "lead" }, "Switch to the LDC role to approve the kit and the leader messages.") : null,
    feedback);
}

async function drawCase(root, caseId, show) {
  const view = await api.case(caseId);
  const now = view.case.state;
  const reached = PATH.indexOf(now);
  root.append(el("section", { class: "card" },
    el("h2", {}, [view.case.person_ref, view.case.data.role].filter(Boolean).join(" · ")),
    el("div", { class: "steps", "aria-label": "Case states" }, PATH.map((s, i) =>
      el("span", { class: `step${s === now ? " now" : reached > i ? " done" : ""}` }, STATE_LABELS[s]))),
    PATH.includes(now) ? null : el("p", {}, "Current state: ", statePill(now)),
    timingLine(view.case.package_timing)));

  const followup = followupCard(view, caseId, show);
  if (followup) root.append(followup);
  const info = infoPackageCard(view, caseId, show);
  if (info) root.append(info);
  const igs = igsCard(view, caseId, show);
  if (igs) root.append(igs);

  root.append(el("section", { class: "card" }, el("h2", {}, "Records created after approval"),
    view.records.length
      ? el("div", { class: "list" }, view.records.map((r) => el("div", { class: "row" },
          el("div", {}, el("div", {}, SYSTEMS[r.system] || r.system), el("div", { class: "meta" }, Object.entries(r.data).map(([k, v]) => `${k}: ${v}`).join(" · "))),
          el("span", { class: "mono" }, r.approval_id))))
      : el("p", { class: "empty" }, "Nothing yet. Records appear only after the current package version is approved.")));

  root.append(el("section", { class: "card" }, el("h2", {}, "Audit log"),
    el("div", { class: "table-wrap" }, el("table", {},
      el("thead", {}, el("tr", {}, ["Time", "Agent", "Action", "Outcome", "Version", "Rules used"].map((h) => el("th", {}, h)))),
      el("tbody", {}, view.audit.map((a) => el("tr", {},
        el("td", { class: "mono" }, new Date(a.at).toLocaleTimeString()),
        el("td", {}, a.agent),
        el("td", {}, a.action.replaceAll("_", " ")),
        el("td", {}, el("span", { class: `pill ${a.outcome === "completed" ? "ok" : "bad"}` }, a.outcome)),
        el("td", {}, a.package_version ? `v${a.package_version}` : "—"),
        el("td", { class: "mono" }, a.rule_ids.join(", ") || "—"))))))));
}
