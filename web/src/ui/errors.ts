/** Lista de errores de compilación. Un clic lleva al lugar del error. */

import { dom } from "../dom";
import { PHASE_LABEL, type CompileError } from "../types";

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

function errorItem(error: CompileError, onSelect: (e: CompileError) => void): HTMLLIElement {
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
  item.addEventListener("click", () => onSelect(error));
  item.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(error);
    }
  });
  return item;
}

export function renderErrors(errors: CompileError[], onSelect: (e: CompileError) => void): void {
  dom.errorList.replaceChildren(...errors.map((e) => errorItem(e, onSelect)));
  dom.errorCount.textContent = errors.length ? String(errors.length) : "";
  dom.errorsEmpty.hidden = errors.length > 0;
}
