import { api, el, errorNotice } from "../../shared/api-client.js";

export async function render(root) {
  root.append(
    el("h1", {}, "Simulated alerts"),
    el("p", { class: "lead" }, "The notifications that would go through Teams or email in production. They name fields, never visa, sponsorship or FLSA values."),
  );
  const list = el("div", { class: "list" });
  root.append(el("section", { class: "card" }, list));
  try {
    const alerts = await api.alerts();
    if (!alerts.length) list.append(el("p", { class: "empty" }, "No alerts yet."));
    for (const alert of alerts) {
      list.append(el("div", { class: "row" },
        el("div", {}, el("div", {}, alert.text), el("div", { class: "meta" }, `To ${alert.recipient}`)),
        el("span", { class: "meta" }, new Date(alert.at).toLocaleTimeString())));
    }
  } catch (error) {
    list.append(errorNotice(error));
  }
}
