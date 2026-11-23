/** Pestañas de archivos sobre el editor. Clic abre, clic central o × cierra,
 *  doble clic (o F2 con la pestaña enfocada) renombra en el lugar. */

import { dom } from "../dom";
import { activeFile, allFiles, renameFile, type SourceFile } from "../files";
import { showToast } from "./toast";

export interface FileTabsHandlers {
  select(id: string): void;
  close(id: string): void;
  create(): void;
}

let handlers: FileTabsHandlers | null = null;
// Mientras se renombra una pestaña no se vuelve a pintar la lista.
let renaming: string | null = null;

function closeButton(file: SourceFile): HTMLButtonElement {
  const button = document.createElement("button");
  button.className = "file-tab-close";
  button.type = "button";
  button.tabIndex = -1;
  button.title = `Cerrar ${file.name}`;
  button.setAttribute("aria-label", `Cerrar ${file.name}`);
  button.textContent = "×";
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    handlers?.close(file.id);
  });
  return button;
}

function startRename(tab: HTMLElement, file: SourceFile): void {
  renaming = file.id;
  const label = tab.querySelector<HTMLElement>(".file-tab-name")!;
  const input = document.createElement("input");
  input.className = "file-tab-input";
  input.value = file.name;
  input.spellcheck = false;
  input.setAttribute("aria-label", "Nuevo nombre del archivo");
  input.size = Math.max(file.name.length, 6);
  label.replaceWith(input);
  input.focus();
  // Selecciona el nombre sin la extensión, como un explorador de archivos.
  input.setSelectionRange(0, file.name.lastIndexOf(".") > 0 ? file.name.lastIndexOf(".") : file.name.length);

  let done = false;
  const finish = (apply: boolean) => {
    if (done) return;
    done = true;
    renaming = null;
    const problem = apply ? renameFile(file.id, input.value) : null;
    if (problem) showToast(problem);
    renderFileTabs();
    dom.fileTabs.querySelector<HTMLElement>(`[data-id="${file.id}"]`)?.focus();
  };
  input.addEventListener("keydown", (event) => {
    event.stopPropagation();
    if (event.key === "Enter") finish(true);
    if (event.key === "Escape") finish(false);
  });
  input.addEventListener("input", () => (input.size = Math.max(input.value.length, 6)));
  input.addEventListener("blur", () => finish(true));
  input.addEventListener("click", (event) => event.stopPropagation());
}

function tabElement(file: SourceFile, active: boolean): HTMLElement {
  const tab = document.createElement("div");
  tab.className = "file-tab";
  tab.dataset.id = file.id;
  tab.setAttribute("role", "tab");
  tab.setAttribute("aria-selected", String(active));
  tab.tabIndex = active ? 0 : -1;
  tab.title = active ? `${file.name} · doble clic para renombrar` : file.name;
  if (active) tab.classList.add("is-active");

  const name = document.createElement("span");
  name.className = "file-tab-name";
  name.textContent = file.name;
  tab.append(name, closeButton(file));

  tab.addEventListener("click", () => handlers?.select(file.id));
  tab.addEventListener("auxclick", (event) => {
    if (event.button === 1) handlers?.close(file.id);
  });
  tab.addEventListener("mousedown", (event) => {
    if (event.button === 1) event.preventDefault(); // sin autoscroll
  });
  tab.addEventListener("dblclick", () => startRename(tab, file));
  tab.addEventListener("keydown", (event) => onTabKey(event, tab, file));
  return tab;
}

/** Flechas para moverse entre pestañas, Enter para abrir, F2 renombra y
 *  Supr cierra. */
function onTabKey(event: KeyboardEvent, tab: HTMLElement, file: SourceFile): void {
  const tabs = [...dom.fileTabs.querySelectorAll<HTMLElement>(".file-tab")];
  const index = tabs.indexOf(tab);
  const focus = (i: number) => tabs[(i + tabs.length) % tabs.length]?.focus();
  switch (event.key) {
    case "ArrowRight":
      focus(index + 1);
      break;
    case "ArrowLeft":
      focus(index - 1);
      break;
    case "Enter":
    case " ":
      handlers?.select(file.id);
      break;
    case "F2":
      startRename(tab, file);
      break;
    case "Delete":
      handlers?.close(file.id);
      break;
    default:
      return;
  }
  event.preventDefault();
}

export function renderFileTabs(): void {
  if (renaming) return;
  const active = activeFile()?.id;
  const tabs = allFiles().map((file) => tabElement(file, file.id === active));
  dom.fileTabs.replaceChildren(...tabs);
  dom.fileTabs.querySelector(".is-active")?.scrollIntoView({ block: "nearest", inline: "nearest" });
}

/** Renombrar el archivo activo desde el menú. */
export function renameActiveTab(): void {
  const file = activeFile();
  if (!file) return;
  const tab = dom.fileTabs.querySelector<HTMLElement>(`[data-id="${file.id}"]`);
  if (tab) startRename(tab, file);
}

export function initFileTabs(h: FileTabsHandlers): void {
  handlers = h;
  dom.newFileButton.addEventListener("click", () => handlers?.create());
  renderFileTabs();
}
