// Talks only to the local API. The role travels in X-Role; the server decides
// what each role may see and do.
function savedRole() {
  try { return localStorage.getItem("role") || "recruiter"; } catch { return "recruiter"; }
}
const state = { role: savedRole(), caseId: null };

export function getRole() { return state.role; }
export function setRole(role) {
  state.role = role;
  try { localStorage.setItem("role", role); } catch { /* private mode */ }
}
export function getCase() { return state.caseId; }
export function setCase(id) { state.caseId = id; }

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
    this.status = status;
    this.detail = detail;
  }
}

async function call(method, path, body) {
  const response = await fetch(path, {
    method,
    headers: { "X-Role": state.role, ...(body ? { "Content-Type": "application/json" } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, data.detail ?? response.statusText);
  return data;
}

export const api = {
  inbox: () => call("GET", "/api/inbox"),
  sendEmail: (sender, subject, body) => call("POST", "/api/inbox", { sender, subject, body }),
  process: (id) => call("POST", `/api/inbox/${encodeURIComponent(id)}/process`),
  cases: () => call("GET", "/api/cases"),
  rule: (id) => call("GET", `/api/rules/${encodeURIComponent(id)}`),
  dashboard: () => call("GET", "/api/cases/dashboard"),
  case: (id) => call("GET", `/api/cases/${encodeURIComponent(id)}`),
  answer: (id, field, value) => call("POST", `/api/cases/${encodeURIComponent(id)}/answers`, { field, value }),
  decide: (id, packageVersion, decision, comment) =>
    call("POST", `/api/cases/${encodeURIComponent(id)}/decision`, { package_version: packageVersion, decision, comment }),
  assignOwner: (id, owner) => call("POST", `/api/cases/${encodeURIComponent(id)}/owner`, { owner }),
  approveIt: (id, packageVersion) => call("POST", `/api/cases/${encodeURIComponent(id)}/it-approval`, { package_version: packageVersion }),
  hrAnswer: (id, field, value) => call("POST", `/api/cases/${encodeURIComponent(id)}/hr-answer`, { field, value }),
  review: (id, field, action, values) => call("POST", `/api/cases/${encodeURIComponent(id)}/recommendation`, { field, action, values: values || [] }),
  runFollowup: (id, atHours) => call("POST", `/api/cases/${encodeURIComponent(id)}/followup/run`, { at_hours: atHours }),
  deliver: (id, items) => call("POST", `/api/cases/${encodeURIComponent(id)}/documents`, { items }),
  countersign: (id, item) => call("POST", `/api/cases/${encodeURIComponent(id)}/documents/countersign`, { item }),
  payrollHandoff: (id, packageVersion) => call("POST", `/api/cases/${encodeURIComponent(id)}/payroll-handoff`, { package_version: packageVersion }),
  payrollReturn: (id, issue) => call("POST", `/api/cases/${encodeURIComponent(id)}/payroll-returns`, { issue }),
  approveKit: (id, packageVersion) => call("POST", `/api/cases/${encodeURIComponent(id)}/welcome-kit`, { package_version: packageVersion }),
  runIgs: (id, atDays) => call("POST", `/api/cases/${encodeURIComponent(id)}/igs/run`, { at_days: atDays }),
  approveLeaderMessage: (id, messageId) => call("POST", `/api/cases/${encodeURIComponent(id)}/leader-messages/${messageId}/approval`),
  prepareInfoPackage: (id) => call("POST", `/api/cases/${encodeURIComponent(id)}/info-package`),
  sendInfoPackage: (id) => call("POST", `/api/cases/${encodeURIComponent(id)}/info-package/send`),
  chat: (message, caseId) => call("POST", "/api/chat", { message, case_id: caseId || null }),
  knowledge: () => call("GET", "/api/knowledge"),
  askKnowledge: (question) => call("POST", "/api/knowledge/ask", { question }),
  validateKnowledge: (id, decision) => call("POST", `/api/knowledge/${encodeURIComponent(id)}/validation`, { decision }),
  alerts: (caseId) => call("GET", `/api/alerts${caseId ? `?case_id=${encodeURIComponent(caseId)}` : ""}`),
};

// Small DOM helper: text only, never innerHTML.
export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (value !== false && value != null) node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat()) {
    if (child == null || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

export const STATE_LABELS = {
  received: "Received", blocked_duplicate: "Blocked: duplicate", validated: "Validated",
  needs_clarification: "Needs clarification", case_set_up: "Case set up",
  ready_for_review: "Ready for review", approval_gate: "Approval gate", approved: "Approved",
  rejected: "Rejected", actions_executed: "Actions executed", documents_pending: "Documents pending",
  in_verification: "In verification", sent_to_payroll: "Sent to payroll", closed: "Closed",
};

export function statePill(stateName) {
  const tone = { actions_executed: "ok", approved: "ok", sent_to_payroll: "ok", documents_pending: "warn", in_verification: "warn", ready_for_review: "warn",
    needs_clarification: "warn", rejected: "bad", blocked_duplicate: "bad" }[stateName] || "neutral";
  return el("span", { class: `pill ${tone}` }, STATE_LABELS[stateName] || stateName);
}

export function errorNotice(error) {
  if (error.status === 409 && error.detail?.refused) {
    const current = error.detail.current_version ? ` The current version is v${error.detail.current_version}.` : "";
    return el("div", { class: "notice bad", role: "alert" }, `Refused: ${error.detail.refused.replaceAll("_", " ")}.${current}`);
  }
  if (error.status === 400 && Array.isArray(error.detail)) {
    const fields = error.detail.map((e) => `${e.field}: ${e.message}`).join("; ");
    return el("div", { class: "notice bad", role: "alert" }, `Please check ${fields}.`);
  }
  if (error.status === 403) return el("div", { class: "notice bad", role: "alert" }, "Your role cannot do this. Switch to the Approver role.");
  return el("div", { class: "notice bad", role: "alert" }, `Something went wrong: ${error.message}`);
}
