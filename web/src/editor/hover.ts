/** Tipo al pasar el mouse: muestra qué es cada identificador según la
 *  última compilación. Variables, parámetros y constantes muestran su tipo;
 *  funciones, structs, enums y variantes, su declaración. */

import { MapMode, StateEffect, StateField, type Text } from "@codemirror/state";
import { hoverTooltip, type EditorView } from "@codemirror/view";

import type { SymbolHint } from "../types";

interface HintRange {
  from: number;
  to: number;
  hint: SymbolHint;
}

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

export const setSymbols = StateEffect.define<HintRange[]>();

/** Las posiciones se mueven con las ediciones hasta la próxima compilación.
 *  Si se borra el nombre, su pista desaparece. */
const symbolsField = StateField.define<HintRange[]>({
  create: () => [],
  update(ranges, tr) {
    for (const effect of tr.effects) if (effect.is(setSymbols)) return effect.value;
    if (!tr.docChanged) return ranges;
    return ranges.flatMap((range) => {
      const from = tr.changes.mapPos(range.from, 1, MapMode.TrackDel);
      const to = tr.changes.mapPos(range.to, -1, MapMode.TrackDel);
      return from === null || to === null || to <= from ? [] : [{ ...range, from, to }];
    });
  },
});

/** Convierte las posiciones del compilador (línea y columna desde 1). */
export function toRanges(doc: Text, hints: SymbolHint[]): HintRange[] {
  return hints.flatMap((hint) => {
    if (hint.line < 1 || hint.line > doc.lines) return [];
    const line = doc.line(hint.line);
    const from = line.from + hint.column - 1;
    const to = from + hint.length;
    return to <= line.to ? [{ from, to, hint }] : [];
  });
}

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
  return dom;
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
