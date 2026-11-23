/** Tipo al pasar el mouse: muestra qué es cada identificador según la
 *  última compilación. Variables, parámetros y constantes muestran su tipo;
 *  funciones, structs, enums y variantes, su declaración. */

import { hoverTooltip, type EditorView } from "@codemirror/view";

import type { SymbolHint } from "../types";
import { symbolsField } from "./symbols";

const KIND_LABEL: Record<SymbolHint["kind"], string> = {
  local: "variable local",
  param: "parámetro",
  const: "constante",
  func: "función",
  host: "función del host",
  struct: "struct",
  enum: "enum",
  variant: "variante",
};

/** Cómo se escribiría la declaración: `let mut x: i32`, `fn suma(...)`. */
function signatureText(hint: SymbolHint): string {
  const type = hint.type ?? "?";
  switch (hint.kind) {
    case "func":
    case "host":
    case "struct":
    case "enum":
    case "variant":
      return type;
    case "const":
      return `const ${hint.name}: ${type}`;
    case "param":
      return `${hint.mutable ? "mut " : ""}${hint.name}: ${type}`;
    case "local":
      return `let ${hint.mutable ? "mut " : ""}${hint.name}: ${type}`;
  }
}

function detailText(hint: SymbolHint): string {
  const parts = [KIND_LABEL[hint.kind]];
  if (hint.mutable) parts.push("mutable");
  if (hint.type === null) parts.push("tipo desconocido por un error");
  return parts.join(" · ");
}

function tooltipDom(hint: SymbolHint): HTMLElement {
  const dom = document.createElement("div");
  dom.className = "cm-symbol-hover";
  const code = document.createElement("code");
  code.className = "cm-symbol-signature";
  code.textContent = signatureText(hint);
  const detail = document.createElement("div");
  detail.className = "cm-symbol-detail";
  detail.textContent = detailText(hint);
  dom.append(code, detail);
  // Las funciones del host no tienen declaración en el programa.
  if (hint.kind !== "host") {
    const keys = document.createElement("div");
    keys.className = "cm-symbol-keys";
    keys.append(...shortcut("F12", "definición"), ...shortcut("⇧F12", "referencias"), ...shortcut("F2", "renombrar"));
    dom.append(keys);
  }
  return dom;
}

function shortcut(key: string, label: string): Node[] {
  const kbd = document.createElement("kbd");
  kbd.textContent = key;
  return [kbd, document.createTextNode(` ${label}`)];
}

const symbolHover = hoverTooltip((view: EditorView, pos: number, side: -1 | 1) => {
  const range = view.state.field(symbolsField).find(
    (r) => (r.from < pos || (r.from === pos && side > 0)) && (r.to > pos || (r.to === pos && side < 0)),
  );
  // Si se editó el nombre desde la última compilación, la pista ya no vale.
  if (!range || view.state.sliceDoc(range.from, range.to) !== range.hint.name) return null;
  return { pos: range.from, end: range.to, above: true, create: () => ({ dom: tooltipDom(range.hint) }) };
});

export const symbolHoverExtension = [symbolsField, symbolHover];
