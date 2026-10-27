import { api, el, errorNotice, setCase } from "../../shared/api-client.js";

// US-030: every case under its current state, with who acts next and its risks.
export async function render(root, show) {
  root.append(
    el("h1", {}, "Dashboard"),
    el("p", { class: "lead" }, "Every case under its current state, with what is pending and its risks. Select a case to open it."),
  );
  const board = el("div", { class: "board" });
  root.append(board);
  let columns;
  try {
    columns = await api.dashboard();
  } catch (error) {
    board.append(errorNotice(error));
    return;
  }
  if (!columns.length) board.append(el("p", { class: "empty" }, "No cases yet. Start one from the simulated inbox."));
  for (const column of columns) {
    board.append(el("section", { class: "card board-column", "aria-label": column.label },
      el("h2", {}, `${column.label} `, el("span", { class: "meta" }, `(${column.cases.length})`)),
      el("div", { class: "list" }, column.cases.map((item) => {
        const open = () => { setCase(item.id); show("status"); };
        return el("div", { class: "row clickable board-case", tabindex: "0", onclick: open,
          onkeydown: (e) => { if (e.key === "Enter") open(); } },
          el("div", {},
            el("div", {}, el("span", { class: "mono" }, item.person_ref), el("span", { class: "meta" }, ` · starts ${item.start_date}`)),
            item.pending.map((p) => el("div", { class: "meta" }, `• ${p}`)),
            (item.done || []).map((d) => el("div", { class: "meta done" }, `✓ ${d}`)),
            el("div", { class: "actions" }, item.risks.map((r) => el("span", { class: "pill bad" }, r)))));
      }))));
  }
}
