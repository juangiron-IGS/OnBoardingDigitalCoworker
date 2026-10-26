import { api, el, errorNotice, getCase, setCase, statePill, STATE_LABELS } from "../../shared/api-client.js";

const PATH = ["received", "validated", "case_set_up", "ready_for_review", "approval_gate", "approved", "actions_executed"];
const SYSTEMS = { jobdiva_cases: "JobDiva case (mock)", task_lists: "Onboarding task list", it_requests: "IT request (mock)" };

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
  if (getCase()) await drawCase(detail, getCase());
}

async function drawCase(root, caseId) {
  const view = await api.case(caseId);
  const now = view.case.state;
  const reached = PATH.indexOf(now);
  root.append(el("section", { class: "card" },
    el("h2", {}, `${view.case.person_ref} · ${view.case.id}`),
    el("div", { class: "steps", "aria-label": "Case states" }, PATH.map((s, i) =>
      el("span", { class: `step${s === now ? " now" : reached > i ? " done" : ""}` }, STATE_LABELS[s]))),
    PATH.includes(now) ? null : el("p", {}, "Current state: ", statePill(now))));

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
