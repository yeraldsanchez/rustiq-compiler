/** Lista de errores de compilación. Un clic lleva al lugar del error; los
 *  que tienen arreglo rápido muestran un botón para aplicarlo. */

import { dom } from "../dom";
import type { QuickFix } from "../editor/quickFixes";
import { PHASE_LABEL, type CompileError } from "../types";

export interface ErrorListHandlers {
  select(error: CompileError): void;
  fixes(error: CompileError): QuickFix[];
  applyFix(error: CompileError, fix: QuickFix): void;
}

// Los mensajes del compilador citan código entre comillas simples: 'p'.
const QUOTED = /'([^']+)'/g;

/** Arma el mensaje con lo citado en <code>, sin usar innerHTML. */
function messageNodes(message: string): Node[] {
  const nodes: Node[] = [];
  let last = 0;
  for (const match of message.matchAll(QUOTED)) {
    nodes.push(document.createTextNode(message.slice(last, match.index)));
    const code = document.createElement("code");
    code.textContent = match[1];
    nodes.push(code);
    last = match.index + match[0].length;
  }
  nodes.push(document.createTextNode(message.slice(last)));
  return nodes;
}

function fixButtons(error: CompileError, handlers: ErrorListHandlers): HTMLElement | null {
  const fixes = handlers.fixes(error);
  if (!fixes.length) return null;
  const row = document.createElement("div");
  row.className = "error-fixes";
  for (const fix of fixes) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "error-fix";
    button.append(...messageNodes(fix.label));
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      handlers.applyFix(error, fix);
    });
    button.addEventListener("keydown", (event) => event.stopPropagation());
    row.append(button);
  }
  return row;
}

function errorItem(error: CompileError, handlers: ErrorListHandlers): HTMLLIElement {
  const onSelect = handlers.select;
  const item = document.createElement("li");
  item.className = "error-item";
  item.tabIndex = 0;

  const pos = document.createElement("span");
  pos.className = "error-pos";
  pos.textContent = `${error.line}:${error.column}`;

  const message = document.createElement("p");
  message.className = "error-msg";
  message.append(...messageNodes(error.message));

  const meta = document.createElement("span");
  meta.className = "error-meta";
  meta.textContent = `${PHASE_LABEL[error.phase]} · ${error.code}`;

  item.append(pos, message, meta);
  const fixes = fixButtons(error, handlers);
  if (fixes) item.append(fixes);
  item.addEventListener("click", () => onSelect(error));
  item.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(error);
    }
  });
  return item;
}

export function renderErrors(errors: CompileError[], handlers: ErrorListHandlers): void {
  dom.errorList.replaceChildren(...errors.map((e) => errorItem(e, handlers)));
  dom.errorCount.textContent = errors.length ? String(errors.length) : "";
  dom.errorsEmpty.hidden = errors.length > 0;
}
