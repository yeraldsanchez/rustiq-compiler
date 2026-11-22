/** Panel de salida con dos pestañas: lo que imprime el programa y el WAT.
 *  También copia y descarga el resultado de la última compilación. */

import { dom } from "../dom";
import { createWatView } from "../editor/watView";

type Tab = "output" | "wat";

const COPIED_FEEDBACK_MS = 1200;
const COPY_LABEL = "Copiar";

let activeTab: Tab = "output";
let wat: string | null = null;
let wasm: Uint8Array<ArrayBuffer> | null = null;

// La salida llega línea por línea desde el Worker. Se junta y se pinta una
// vez por cuadro para no tocar el DOM miles de veces.
let pending: string[] = [];
let consoleText: HTMLPreElement | null = null;
let frame = 0;

const watView = createWatView(dom.watHost);

function emptyMessage(text: string): HTMLParagraphElement {
  const p = document.createElement("p");
  p.className = "empty";
  p.textContent = text;
  return p;
}

function line(text: string, className: string): HTMLPreElement {
  const pre = document.createElement("pre");
  pre.className = className;
  pre.textContent = text;
  return pre;
}

function flush(): void {
  frame = 0;
  if (!pending.length) return;
  if (!consoleText) {
    consoleText = line("", "stdout");
    dom.paneOutput.append(consoleText);
  }
  consoleText.append(pending.join("\n") + "\n");
  pending = [];
  dom.paneOutput.scrollTop = dom.paneOutput.scrollHeight;
}

function refreshTools(): void {
  dom.copyButton.disabled = activeTab === "wat" ? wat === null : !dom.paneOutput.querySelector("pre");
  dom.downloadWatButton.disabled = wat === null;
  dom.downloadWasmButton.disabled = wasm === null;
}

export function selectTab(tab: Tab): void {
  activeTab = tab;
  const isOutput = tab === "output";
  dom.tabOutput.classList.toggle("is-active", isOutput);
  dom.tabWat.classList.toggle("is-active", !isOutput);
  dom.tabOutput.setAttribute("aria-selected", String(isOutput));
  dom.tabWat.setAttribute("aria-selected", String(!isOutput));
  dom.paneOutput.hidden = !isOutput;
  dom.paneWat.hidden = isOutput;
  refreshTools();
}

/** Guarda el resultado de una compilación (o lo borra si falló). */
export function setModule(newWat: string | null, newWasm: Uint8Array<ArrayBuffer> | null): void {
  wat = newWat;
  wasm = newWasm;
  dom.watHost.hidden = wat === null;
  dom.watEmpty.hidden = wat !== null;
  if (wat === null) dom.watEmpty.textContent = "No hay WAT: el programa tiene errores de compilación.";
  else watView.setText(wat);
  refreshTools();
}

export function clearOutput(): void {
  pending = [];
  consoleText = null;
  dom.paneOutput.replaceChildren();
  refreshTools();
}

export function showOutputMessage(text: string): void {
  clearOutput();
  dom.paneOutput.append(emptyMessage(text));
}

export function printLine(text: string): void {
  pending.push(text);
  if (!frame) frame = requestAnimationFrame(flush);
}

/** Nota final después de la salida del programa: fin, trap, tiempo agotado. */
export function appendNote(text: string, kind: "note" | "trap"): void {
  cancelAnimationFrame(frame);
  flush();
  consoleText = null;
  dom.paneOutput.append(line(text, kind));
  dom.paneOutput.scrollTop = dom.paneOutput.scrollHeight;
  refreshTools();
}

function download(data: BlobPart, filename: string, type: string): void {
  const url = URL.createObjectURL(new Blob([data], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

async function copyActive(): Promise<void> {
  const text = activeTab === "wat" ? (wat ?? "") : dom.paneOutput.innerText;
  try {
    await navigator.clipboard.writeText(text);
    dom.copyButton.textContent = "Copiado";
  } catch {
    dom.copyButton.textContent = "No se pudo";
  }
  setTimeout(() => (dom.copyButton.textContent = COPY_LABEL), COPIED_FEEDBACK_MS);
}

dom.tabOutput.addEventListener("click", () => selectTab("output"));
dom.tabWat.addEventListener("click", () => selectTab("wat"));
dom.copyButton.addEventListener("click", () => void copyActive());
dom.downloadWatButton.addEventListener("click", () => wat !== null && download(wat, "main.wat", "text/plain"));
dom.downloadWasmButton.addEventListener("click", () => wasm && download(wasm, "main.wasm", "application/wasm"));
