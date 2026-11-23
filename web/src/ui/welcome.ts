/** Inicio del editor cuando no hay archivos abiertos: crear, abrir desde el
 *  disco, abrir un ejemplo y volver a abrir los cerrados hace poco. */

import { dom } from "../dom";
import type { ClosedFile } from "../files";

export interface WelcomeActions {
  create(): void;
  openFromDisk(): void;
  openExamples(): void;
  reopen(id: string): void;
}

let actions: WelcomeActions | null = null;

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/** "hace 3 min", "hace 2 h", "hace 1 día". */
function ago(timestamp: number): string {
  const elapsed = Math.max(0, Date.now() - timestamp);
  if (elapsed < MINUTE) return "hace un momento";
  if (elapsed < HOUR) return `hace ${Math.floor(elapsed / MINUTE)} min`;
  if (elapsed < DAY) return `hace ${Math.floor(elapsed / HOUR)} h`;
  const days = Math.floor(elapsed / DAY);
  return days === 1 ? "hace 1 día" : `hace ${days} días`;
}

function recentItem(file: ClosedFile): HTMLLIElement {
  const item = document.createElement("li");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "welcome-recent-file";
  button.textContent = file.name;
  button.addEventListener("click", () => actions?.reopen(file.id));
  const when = document.createElement("span");
  when.className = "welcome-when";
  when.textContent = ago(file.closedAt);
  item.append(button, when);
  return item;
}

/** Muestra el inicio (sin archivos) o el editor. */
export function showWelcome(visible: boolean, recent: readonly ClosedFile[]): void {
  dom.welcome.hidden = !visible;
  dom.editor.hidden = visible;
  dom.editorHead.classList.toggle("is-empty", visible);
  dom.editorStatus.hidden = visible;
  if (!visible) return;
  dom.recentList.replaceChildren(...recent.map(recentItem));
  dom.welcomeRecent.hidden = recent.length === 0;
}

export function initWelcome(handlers: WelcomeActions): void {
  actions = handlers;
  dom.welcomeNew.addEventListener("click", () => actions?.create());
  dom.welcomeOpen.addEventListener("click", () => actions?.openFromDisk());
  dom.welcomeExamples.addEventListener("click", () => actions?.openExamples());
}
