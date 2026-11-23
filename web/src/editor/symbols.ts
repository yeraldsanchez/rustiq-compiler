/** Los identificadores de la última compilación, guardados en el estado del
 *  editor. Las posiciones se mueven con las ediciones hasta la próxima
 *  compilación; una aparición cuyo texto ya no coincide con su nombre se
 *  considera vieja y no se usa. De aquí leen el hover, la navegación y los
 *  arreglos rápidos. */

import { MapMode, StateEffect, StateField, type EditorState, type Text } from "@codemirror/state";

import type { SymbolHint } from "../types";

export interface HintRange {
  from: number;
  to: number;
  hint: SymbolHint;
}

export const setSymbols = StateEffect.define<HintRange[]>();

export const symbolsField = StateField.define<HintRange[]>({
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

/** El texto sigue siendo el nombre que vio el compilador. */
export function isFresh(state: EditorState, range: HintRange): boolean {
  return state.sliceDoc(range.from, range.to) === range.hint.name;
}

/** La aparición que toca `pos` (incluye los dos bordes del nombre). */
export function symbolAt(state: EditorState, pos: number): HintRange | null {
  const range = state.field(symbolsField).find((r) => r.from <= pos && pos <= r.to);
  return range && isFresh(state, range) ? range : null;
}

/** Todas las apariciones del mismo nombre, en orden. `stale` indica que
 *  alguna cambió desde la última compilación. */
export function occurrences(state: EditorState, id: string): { ranges: HintRange[]; stale: boolean } {
  const ranges = state.field(symbolsField).filter((r) => r.hint.id === id);
  return { ranges, stale: ranges.some((r) => !isFresh(state, r)) };
}

export function declarationOf(state: EditorState, id: string): HintRange | null {
  const range = state.field(symbolsField).find((r) => r.hint.id === id && r.hint.declaration);
  return range && isFresh(state, range) ? range : null;
}
