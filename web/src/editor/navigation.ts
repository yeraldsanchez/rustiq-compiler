/** Navegación por los nombres del programa: resaltar las apariciones del que
 *  está bajo el cursor, ir a su definición, listar sus referencias y
 *  renombrarlo. Todo sale de los `id` que manda el compilador, así que dos
 *  variables con el mismo nombre en ámbitos distintos no se confunden. */

import { EditorSelection, StateField, type EditorState } from "@codemirror/state";
import { Decoration, EditorView, type DecorationSet } from "@codemirror/view";

import { KEYWORDS } from "./completion";
import { declarationOf, occurrences, symbolAt, symbolsField, type HintRange } from "./symbols";

export interface Reference {
  from: number;
  to: number;
  line: number;
  column: number;
  /** El texto de la línea, sin la sangría. */
  preview: string;
  declaration: boolean;
}

/** Lo que la navegación necesita de afuera: recompilar para tener símbolos
 *  frescos y mostrar listas, avisos y el cuadro de renombrar. */
export interface NavigationHost {
  refreshSymbols(): Promise<void>;
  showReferences(name: string, references: Reference[], anchor: DOMRect): void;
  promptRename(name: string, anchor: DOMRect, submit: (newName: string) => string | null): void;
  notify(message: string): void;
}

const IDENTIFIER = /^[A-Za-z_][A-Za-z0-9_]*$/;
const MAIN = "main";

// --- Resaltado de apariciones ----------------------------------------------

const occurrenceMark = Decoration.mark({ class: "cm-symbol-occurrence" });
const declarationMark = Decoration.mark({ class: "cm-symbol-occurrence cm-symbol-occurrence-decl" });

function occurrenceDecorations(state: EditorState): DecorationSet {
  const selection = state.selection.main;
  if (!selection.empty) return Decoration.none;
  const current = symbolAt(state, selection.head);
  if (!current) return Decoration.none;
  const { ranges } = occurrences(state, current.hint.id);
  // Un nombre que aparece una sola vez no tiene nada que señalar.
  if (ranges.length < 2) return Decoration.none;
  return Decoration.set(
    ranges
      .filter((r) => state.sliceDoc(r.from, r.to) === r.hint.name)
      .map((r) => (r.hint.declaration ? declarationMark : occurrenceMark).range(r.from, r.to)),
    true,
  );
}

const occurrenceField = StateField.define<DecorationSet>({
  create: occurrenceDecorations,
  update(value, tr) {
    const symbolsChanged = tr.startState.field(symbolsField) !== tr.state.field(symbolsField);
    return tr.docChanged || tr.selection || symbolsChanged ? occurrenceDecorations(tr.state) : value;
  },
  provide: (field) => EditorView.decorations.from(field),
});

// --- Utilidades ------------------------------------------------------------

function select(view: EditorView, range: { from: number; to: number }): void {
  view.dispatch({
    selection: EditorSelection.range(range.from, range.to),
    effects: EditorView.scrollIntoView(range.from, { y: "center" }),
  });
  view.focus();
}

function anchorAt(view: EditorView, pos: number): DOMRect {
  const coords = view.coordsAtPos(pos) ?? view.coordsAtPos(view.state.selection.main.head);
  if (!coords) return view.dom.getBoundingClientRect();
  return new DOMRect(coords.left, coords.top, Math.max(coords.right - coords.left, 1), coords.bottom - coords.top);
}

/** El nombre bajo el cursor. Si no hay símbolos frescos (nunca se compiló o
 *  el código cambió), recompila una vez y vuelve a buscar. */
async function currentSymbol(view: EditorView, host: NavigationHost, pos?: number): Promise<HintRange | null> {
  const at = () => symbolAt(view.state, pos ?? view.state.selection.main.head);
  const found = at();
  if (found && !occurrences(view.state, found.hint.id).stale) return found;
  await host.refreshSymbols();
  return at();
}

function toReference(state: EditorState, range: HintRange): Reference {
  const line = state.doc.lineAt(range.from);
  return {
    from: range.from,
    to: range.to,
    line: line.number,
    column: range.from - line.from + 1,
    preview: line.text.trim(),
    declaration: range.hint.declaration,
  };
}

// --- Acciones --------------------------------------------------------------

export async function goToDefinition(view: EditorView, host: NavigationHost, pos?: number): Promise<void> {
  const symbol = await currentSymbol(view, host, pos);
  if (!symbol) return host.notify("No hay un nombre del programa en el cursor.");
  if (symbol.hint.kind === "host") {
    return host.notify(`'${symbol.hint.name}' es una función del host: la da el entorno, no tu programa.`);
  }
  const declaration = declarationOf(view.state, symbol.hint.id);
  if (!declaration) return host.notify(`No se encontró la declaración de '${symbol.hint.name}'.`);
  // Desde la propia declaración, lo útil es ver dónde se usa.
  if (declaration.from === symbol.from) return findReferences(view, host, pos);
  select(view, declaration);
}

export async function findReferences(view: EditorView, host: NavigationHost, pos?: number): Promise<void> {
  const symbol = await currentSymbol(view, host, pos);
  if (!symbol) return host.notify("No hay un nombre del programa en el cursor.");
  const { ranges } = occurrences(view.state, symbol.hint.id);
  const references = ranges.map((r) => toReference(view.state, r));
  host.showReferences(symbol.hint.name, references, anchorAt(view, symbol.from));
}

export function jumpTo(view: EditorView, reference: { from: number; to: number }): void {
  select(view, reference);
}

function renameProblem(state: EditorState, symbol: HintRange, newName: string): string | null {
  if (!IDENTIFIER.test(newName)) return "Un nombre empieza con letra o _ y solo lleva letras, dígitos y _.";
  if (KEYWORDS.includes(newName)) return `'${newName}' es una palabra reservada.`;
  if (newName === symbol.hint.name) return null;
  // Las variables pueden sombrearse; funciones, tipos y variantes no.
  const namespace = symbol.hint.id.split(":")[0];
  if (namespace === "sym") return null;
  const taken = state.field(symbolsField).some(
    (r) => r.hint.declaration && r.hint.name === newName && r.hint.id.split(":")[0] === namespace,
  );
  if (taken) return `Ya hay otra declaración llamada '${newName}'.`;
  return null;
}

export async function renameSymbol(view: EditorView, host: NavigationHost, pos?: number): Promise<void> {
  const symbol = await currentSymbol(view, host, pos);
  if (!symbol) return host.notify("No hay un nombre del programa en el cursor.");
  if (symbol.hint.kind === "host") return host.notify("Las funciones del host no se pueden renombrar.");
  if (symbol.hint.kind === "func" && symbol.hint.name === MAIN) {
    return host.notify("'main' es el punto de entrada y debe llamarse así.");
  }

  host.promptRename(symbol.hint.name, anchorAt(view, symbol.from), (newName) => {
    const problem = renameProblem(view.state, symbol, newName);
    if (problem) return problem;
    if (newName === symbol.hint.name) return null;
    const { ranges, stale } = occurrences(view.state, symbol.hint.id);
    if (stale) return "El código cambió mientras renombrabas. Cierra y vuelve a intentarlo.";
    view.dispatch({
      changes: ranges.map((r) => ({ from: r.from, to: r.to, insert: newName })),
      userEvent: "input.rename",
    });
    view.focus();
    const count = ranges.length === 1 ? "1 lugar" : `${ranges.length} lugares`;
    host.notify(`'${symbol.hint.name}' ahora se llama '${newName}' (${count}).`);
    void host.refreshSymbols();
    return null;
  });
}

/** Ctrl+clic (Cmd+clic en Mac) sobre un nombre va a su definición. Si no hay
 *  nombre debajo, el clic sigue su camino normal (agregar un cursor). */
export function ctrlClickHandler(host: NavigationHost) {
  return EditorView.domEventHandlers({
    mousedown(event, view) {
      if (!(event.ctrlKey || event.metaKey) || event.button !== 0) return false;
      const pos = view.posAtCoords({ x: event.clientX, y: event.clientY });
      if (pos === null || !symbolAt(view.state, pos)) return false;
      event.preventDefault();
      void goToDefinition(view, host, pos);
      return true;
    },
  });
}

export const occurrenceHighlight = occurrenceField;
