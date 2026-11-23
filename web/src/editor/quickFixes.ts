/** Arreglos rápidos: cambios que resuelven un error de compilación con un
 *  clic. Se ofrecen en el tooltip del error y en la lista de errores.
 *
 *  Cada arreglo se decide al compilar, pero se aplica sobre el texto actual:
 *  recibe la posición del error ya movida por las ediciones y vuelve a
 *  comprobar que el texto siga siendo el que causó el error. */

import type { EditorState } from "@codemirror/state";
import type { EditorView } from "@codemirror/view";

import type { CompileError } from "../types";
import { HOST_FUNCTIONS, TYPES } from "./completion";
import { declarationOf, symbolsField, type HintRange } from "./symbols";

export interface QuickFix {
  label: string;
  /** `from` y `to`: dónde está el error ahora. */
  apply(view: EditorView, from: number, to: number): void;
}

type FixFinder = (state: EditorState, error: CompileError, from: number, to: number) => QuickFix[];

const MAX_SUGGESTIONS = 2;
const NEW_MAIN = "\nfn main() {\n}\n";

/** El primer texto entre comillas simples de un mensaje: `'x'`. */
function quoted(message: string, index = 0): string | null {
  return [...message.matchAll(/'([^']+)'/g)][index]?.[1] ?? null;
}

// --- Declarar como mut -----------------------------------------------------

/** `x` no es mut: agrega `mut` en su declaración (`let` o parámetro). */
const makeMutable: FixFinder = (state, error, from) => {
  const name = quoted(error.message);
  if (!name) return [];
  // El error marca el nombre (`x = 1`) o el préstamo entero (`&mut x`): se
  // toma la primera aparición del nombre desde ahí en la misma línea.
  const lineEnd = state.doc.lineAt(from).to;
  const use = state.field(symbolsField).find((r) => r.hint.name === name && r.from >= from && r.from <= lineEnd);
  if (!use || (use.hint.kind !== "local" && use.hint.kind !== "param")) return [];
  const declaration = declarationOf(state, use.hint.id);
  if (!declaration || !canTakeMut(state, declaration)) return [];

  const id = use.hint.id;
  return [
    {
      label: `Declarar '${name}' como mut`,
      apply(view) {
        const current = declarationOf(view.state, id);
        if (!current || !canTakeMut(view.state, current)) return;
        view.dispatch({ changes: { from: current.from, insert: "mut " }, userEvent: "input.fix" });
      },
    },
  ];
};

/** Solo en `let x` y en parámetros; un patrón de `match` no admite `mut`. */
function canTakeMut(state: EditorState, declaration: HintRange): boolean {
  const before = state.sliceDoc(Math.max(0, declaration.from - 8), declaration.from);
  if (/\bmut\s+$/.test(before)) return false;
  if (declaration.hint.kind === "param") return true;
  return /\blet\s+$/.test(before);
}

// --- ¿Quisiste decir...? ---------------------------------------------------

function distance(a: string, b: string): number {
  const row = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    let previous = row[0];
    row[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const current = row[j];
      row[j] = Math.min(row[j] + 1, row[j - 1] + 1, previous + (a[i - 1] === b[j - 1] ? 0 : 1));
      previous = current;
    }
  }
  return row[b.length];
}

/** Los nombres parecidos, del más cercano al más lejano. */
function similar(wrong: string, candidates: Iterable<string>): string[] {
  const limit = Math.max(1, Math.floor(wrong.length / 3));
  const scored = [...new Set(candidates)]
    .filter((c) => c !== wrong)
    .map((c) => ({ c, d: c.toLowerCase() === wrong.toLowerCase() ? 0 : distance(wrong, c) }))
    .filter(({ d }) => d <= limit)
    .sort((x, y) => x.d - y.d || x.c.localeCompare(y.c));
  return scored.slice(0, MAX_SUGGESTIONS).map(({ c }) => c);
}

function declaredNames(state: EditorState, test: (r: HintRange) => boolean): string[] {
  return state.field(symbolsField).filter((r) => r.hint.declaration && test(r)).map((r) => r.hint.name);
}

/** Campos de un struct, leídos de su declaración (`    x: i32,`). */
function structFields(state: EditorState, struct: string): string[] {
  const hint = state.field(symbolsField).find((r) => r.hint.kind === "struct" && r.hint.name === struct)?.hint;
  return [...(hint?.type ?? "").matchAll(/^\s+([A-Za-z_]\w*):/gm)].map((m) => m[1]);
}

function candidatesFor(state: EditorState, error: CompileError, from: number): string[] {
  const { message } = error;
  switch (error.code) {
    case "E_UNDECLARED":
      if (message.startsWith("La función")) {
        return [...declaredNames(state, (r) => r.hint.kind === "func"), ...HOST_FUNCTIONS.map(([name]) => name)];
      }
      // Variables declaradas antes del error, constantes y funciones.
      return declaredNames(state, (r) => r.hint.kind === "const" || r.hint.kind === "func" || r.from < from);
    case "E_UNKNOWN_TYPE": {
      const structs = declaredNames(state, (r) => r.hint.kind === "struct");
      const enums = declaredNames(state, (r) => r.hint.kind === "enum");
      if (message.startsWith("El struct")) return structs;
      if (message.startsWith("El enum")) return enums;
      return [...TYPES, ...structs, ...enums];
    }
    case "E_UNKNOWN_VARIANT": {
      const enumName = quoted(message, 0);
      return declaredNames(state, (r) => r.hint.kind === "variant" && r.hint.id.startsWith(`variant:${enumName}::`));
    }
    case "E_UNKNOWN_FIELD":
      return structFields(state, quoted(message, 0) ?? "");
    default:
      return [];
  }
}

/** El nombre equivocado es el último citado del mensaje. */
function wrongName(error: CompileError): string | null {
  const names = [...error.message.matchAll(/'([^']+)'/g)].map((m) => m[1]);
  return names.at(-1) ?? null;
}

const didYouMean: FixFinder = (state, error, from, to) => {
  const wrong = wrongName(error);
  if (!wrong || state.sliceDoc(from, to) !== wrong) return [];
  return similar(wrong, candidatesFor(state, error, from)).map((name) => ({
    label: `Cambiar por '${name}'`,
    apply(view, at, end) {
      if (view.state.sliceDoc(at, end) !== wrong) return;
      view.dispatch({ changes: { from: at, to: end, insert: name }, userEvent: "input.fix" });
    },
  }));
};

// --- Sintaxis: falta un símbolo --------------------------------------------

/** ANTLR: "missing ';' at 'print_i32'". El símbolo va justo después del
 *  último carácter escrito antes del error, no delante del token siguiente. */
const insertMissing: FixFinder = (_state, error) => {
  const match = /missing '([^']+)' at/.exec(error.message);
  if (!match) return [];
  const symbol = match[1];
  return [
    {
      label: `Insertar '${symbol}'`,
      apply(view, from) {
        const before = view.state.sliceDoc(0, from);
        const at = before.trimEnd().length;
        view.dispatch({ changes: { from: at, insert: symbol }, userEvent: "input.fix" });
      },
    },
  ];
};

// --- Falta main ------------------------------------------------------------

const addMain: FixFinder = (_state, error) => {
  if (error.code !== "E_BAD_MAIN" || !error.message.startsWith("Falta")) return [];
  return [
    {
      label: "Agregar 'fn main()'",
      apply(view) {
        const end = view.state.doc.length;
        const text = view.state.sliceDoc(0, end);
        const insert = text.endsWith("\n") ? NEW_MAIN : `\n${NEW_MAIN}`;
        view.dispatch({ changes: { from: end, insert }, userEvent: "input.fix" });
      },
    },
  ];
};

const FINDERS: Partial<Record<string, FixFinder[]>> = {
  E_ASSIGN_IMMUTABLE: [makeMutable],
  E_BORROW_MUT_IMMUTABLE: [makeMutable],
  E_UNDECLARED: [didYouMean],
  E_UNKNOWN_TYPE: [didYouMean],
  E_UNKNOWN_VARIANT: [didYouMean],
  E_UNKNOWN_FIELD: [didYouMean],
  E_SYNTAX: [insertMissing],
  E_BAD_MAIN: [addMain],
};

/** Los arreglos para un error, con `from`/`to` en el texto de la compilación. */
export function fixesFor(state: EditorState, error: CompileError, from: number, to: number): QuickFix[] {
  return (FINDERS[error.code] ?? []).flatMap((find) => find(state, error, from, to));
}
