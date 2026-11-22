/** Los tres indicadores: estado, tiempo de compilación y tamaño del módulo. */

import { dom } from "../dom";

type Tone = "ok" | "error" | "warn" | "empty" | "neutral";

const TONE_CLASSES = ["is-ok", "is-error", "is-warn", "is-empty"];
const KIB = 1024;

function setStat(element: HTMLElement, text: string, tone: Tone, unit?: string): void {
  element.classList.remove(...TONE_CLASSES);
  if (tone !== "neutral") element.classList.add(`is-${tone}`);
  element.textContent = text;
  if (unit) {
    const small = document.createElement("small");
    small.textContent = unit;
    element.append(small);
  }
}

export function setState(text: string, tone: Tone): void {
  setStat(dom.statState, text, tone);
}

export function setCompileTime(ms: number | null): void {
  if (ms === null) setStat(dom.statTime, "—", "empty");
  else setStat(dom.statTime, String(Math.round(ms)), "neutral", "ms");
}

export function setModuleSize(bytes: number | null): void {
  if (bytes === null) setStat(dom.statSize, "—", "empty");
  else if (bytes < KIB) setStat(dom.statSize, String(bytes), "neutral", "B");
  else setStat(dom.statSize, (bytes / KIB).toFixed(1), "neutral", "KB");
}

export function errorCountLabel(count: number): string {
  return count === 1 ? "1 error" : `${count} errores`;
}
