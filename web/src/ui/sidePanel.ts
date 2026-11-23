/** Panel lateral junto al riel: archivos, esquema y ejemplos. Un clic en un
 *  ícono del riel abre su panel; otro clic en el mismo lo cierra. Arranca
 *  cerrado. Cada panel es una lista (ui/listView.ts) que main.ts llena. */

import { dom } from "../dom";
import { createListView, type ListGroup, type ListView } from "./listView";

export type PanelId = "files" | "outline" | "examples";

export interface PanelSource {
  /** Los grupos de la lista, calculados cada vez que se muestra. */
  groups(): ListGroup[];
  empty?(): string;
}

interface PanelSpec {
  title: string;
  search: boolean;
  placeholder?: string;
  code: boolean;
}

const SPECS: Record<PanelId, PanelSpec> = {
  files: { title: "Archivos", search: false, code: true },
  outline: { title: "Esquema", search: true, placeholder: "Filtrar…", code: true },
  examples: { title: "Ejemplos", search: true, placeholder: "Buscar ejemplo o código…", code: false },
};

let sources: Record<PanelId, PanelSource> | null = null;
let onEscape: () => void = () => {};
const views = new Map<PanelId, ListView>();
let current: PanelId | null = null;

const railButtons = () => [...document.querySelectorAll<HTMLButtonElement>(".rail-btn[data-panel]")];

function viewFor(id: PanelId): ListView {
  let view = views.get(id);
  if (!view) {
    const spec = SPECS[id];
    view = createListView({
      label: spec.title,
      search: spec.search,
      placeholder: spec.placeholder,
      code: spec.code,
      onEscape: () => onEscape(),
    });
    views.set(id, view);
  }
  return view;
}

function render(): void {
  dom.app.classList.toggle("side-open", current !== null);
  dom.side.hidden = current === null;
  for (const button of railButtons()) {
    button.setAttribute("aria-pressed", String(button.dataset.panel === current));
  }
  if (!current || !sources) return;
  const view = viewFor(current);
  dom.sideTitle.textContent = SPECS[current].title;
  dom.sideTools.hidden = current !== "files";
  const source = sources[current];
  if (source.empty) view.setEmptyText(source.empty());
  view.setGroups(source.groups());
  if (dom.sideBody.firstChild !== view.root) dom.sideBody.replaceChildren(view.root);
}

export function openPanel(id: PanelId, focus = false): void {
  current = id;
  render();
  if (focus) viewFor(id).focus();
}

export function closePanel(): void {
  current = null;
  render();
}

export function togglePanel(id: PanelId): void {
  if (current === id) closePanel();
  else openPanel(id, true);
}

/** Vuelve a llenar el panel abierto, si es `id` (o cualquiera, sin `id`). */
export function refreshPanel(id?: PanelId): void {
  if (current && (!id || id === current)) render();
}

export function initSidePanel(panelSources: Record<PanelId, PanelSource>, escape: () => void): void {
  sources = panelSources;
  onEscape = escape;
  for (const button of railButtons()) {
    button.addEventListener("click", () => togglePanel(button.dataset.panel as PanelId));
  }
  render();
}
