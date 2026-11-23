/** Editor de código: CodeMirror 6 con resaltado de Rust, los errores del
 *  compilador marcados en el texto y la navegación por símbolos. Lleva un
 *  documento por archivo abierto, cada uno con su propio historial de
 *  deshacer, sus errores y sus símbolos. */

import { acceptCompletion } from "@codemirror/autocomplete";
import { indentLess, indentMore } from "@codemirror/commands";
import { rust } from "@codemirror/lang-rust";
import { indentUnit } from "@codemirror/language";
import { forEachDiagnostic, lintGutter, setDiagnostics, type Diagnostic } from "@codemirror/lint";
import { EditorSelection, EditorState, Prec, type Extension, type Text } from "@codemirror/state";
import { EditorView, keymap, type Command } from "@codemirror/view";
import { basicSetup } from "codemirror";

import { PHASE_LABEL, type CompileError, type SymbolHint } from "../types";
import { rustiqCompletion } from "./completion";
import { symbolHoverExtension } from "./hover";
import {
  ctrlClickHandler,
  findReferences,
  goToDefinition,
  jumpTo,
  occurrenceHighlight,
  renameSymbol,
  type NavigationHost,
} from "./navigation";
import { outlineOf, type OutlineItem } from "./outline";
import { fixesFor, type QuickFix } from "./quickFixes";
import { setSymbols, toRanges } from "./symbols";
import { editorChrome, rustHighlighting } from "./theme";

// Sangría de 4 espacios, como en Rust.
const INDENT = "    ";

export interface EditorCallbacks extends NavigationHost {
  onChange(source: string): void;
  onCursor(line: number, column: number): void;
  onCompile(): void;
  onRun(): void;
  onOutline(): void;
}

export interface Editor {
  /** Muestra el documento `id`; lo crea con `source` si no existía. */
  open(id: string, source: string): void;
  /** Olvida el documento de un archivo cerrado. */
  forget(id: string): void;
  getSource(): string;
  showErrors(errors: CompileError[]): void;
  /** Pistas para el tipo al pasar el mouse, de la última compilación. */
  showSymbols(symbols: SymbolHint[]): void;
  /** Los arreglos rápidos de un error que se está mostrando. */
  fixesFor(error: CompileError): QuickFix[];
  applyFix(error: CompileError, fix: QuickFix): void;
  outline(): OutlineItem[];
  goTo(line: number, column: number): void;
  select(range: { from: number; to: number }): void;
  focus(): void;
}

export function createEditor(parent: HTMLElement, callbacks: EditorCallbacks): Editor {
  const run = (action: (view: EditorView) => unknown): Command => (view) => (action(view), true);

  const shortcuts = Prec.highest(
    keymap.of([
      { key: "Mod-Enter", run: run(() => callbacks.onRun()) },
      { key: "Mod-b", run: run(() => callbacks.onCompile()) },
      // El código se guarda solo; esto evita el diálogo de guardar del navegador.
      { key: "Mod-s", run: () => true },
      { key: "F12", run: run((view) => goToDefinition(view, callbacks)) },
      { key: "Shift-F12", run: run((view) => findReferences(view, callbacks)) },
      { key: "F2", run: run((view) => renameSymbol(view, callbacks)) },
      { key: "Mod-Shift-o", run: run(() => callbacks.onOutline()) },
      // Tab acepta la sugerencia abierta; si no hay, inserta sangría en vez de
      // mover el foco. Para salir del editor con el teclado: Esc y luego Tab.
      { key: "Tab", run: acceptCompletion },
      { key: "Tab", run: insertTab, shift: indentLess },
    ]),
  );

  const extensions: Extension[] = [
    basicSetup,
    rust(),
    indentUnit.of(INDENT),
    lintGutter(),
    rustiqCompletion,
    symbolHoverExtension,
    occurrenceHighlight,
    ctrlClickHandler(callbacks),
    editorChrome,
    rustHighlighting,
    shortcuts,
    EditorView.updateListener.of((update) => {
      if (update.docChanged) callbacks.onChange(update.state.doc.toString());
      if (update.docChanged || update.selectionSet) reportCursor(update.state);
    }),
  ];

  const view = new EditorView({ parent, state: EditorState.create({ extensions }) });
  const documents = new Map<string, EditorState>();
  let activeId: string | null = null;
  // Arreglos de cada error mostrado. El diagnóstico de CodeMirror sigue la
  // posición del error mientras se edita; desde él se aplica el arreglo.
  let diagnosticOf = new Map<CompileError, { diagnostic: Diagnostic; fixes: QuickFix[] }>();

  function reportCursor(state: EditorState): void {
    const head = state.selection.main.head;
    const line = state.doc.lineAt(head);
    callbacks.onCursor(line.number, head - line.from + 1);
  }

  function toDiagnostic(error: CompileError): Diagnostic {
    const { from, to } = errorRange(view.state.doc, error);
    const fixes = fixesFor(view.state, error, from, to);
    const diagnostic: Diagnostic = {
      from,
      to,
      severity: "error",
      message: error.message,
      source: `${PHASE_LABEL[error.phase]} · ${error.code}`,
      actions: fixes.map((fix) => ({ name: fix.label, apply: (v, f, t) => fix.apply(v, f, t) })),
    };
    diagnosticOf.set(error, { diagnostic, fixes });
    return diagnostic;
  }

  return {
    open(id, source) {
      if (activeId) documents.set(activeId, view.state);
      activeId = id;
      const state = documents.get(id) ?? EditorState.create({ doc: source, extensions });
      documents.set(id, state);
      view.setState(state);
      reportCursor(state);
    },

    forget(id) {
      documents.delete(id);
    },

    getSource: () => view.state.doc.toString(),

    showErrors(errors) {
      diagnosticOf = new Map();
      view.dispatch(setDiagnostics(view.state, errors.map(toDiagnostic)));
    },

    showSymbols(symbols) {
      view.dispatch({ effects: setSymbols.of(toRanges(view.state.doc, symbols)) });
    },

    fixesFor: (error) => diagnosticOf.get(error)?.fixes ?? [],

    applyFix(error, fix) {
      const entry = diagnosticOf.get(error);
      if (!entry) return;
      let applied = false;
      forEachDiagnostic(view.state, (diagnostic, from, to) => {
        if (applied || diagnostic !== entry.diagnostic) return;
        applied = true;
        fix.apply(view, from, to);
      });
      view.focus();
    },

    outline: () => outlineOf(view.state),

    goTo(line, column) {
      const pos = toOffset(view.state.doc, line, column);
      view.dispatch({ selection: EditorSelection.cursor(pos), scrollIntoView: true });
      view.focus();
    },

    select(range) {
      jumpTo(view, range);
    },

    focus: () => view.focus(),
  };
}

/** Sin selección, inserta espacios en el cursor hasta la siguiente columna
 *  múltiplo de la sangría (no mueve el texto que está antes del cursor).
 *  Con texto seleccionado, indenta las líneas completas. */
const insertTab: Command = (view) => {
  const { state } = view;
  if (state.selection.ranges.some((range) => !range.empty)) return indentMore(view);
  const transaction = state.changeByRange((range) => {
    const column = range.head - state.doc.lineAt(range.head).from;
    const spaces = INDENT.length - (column % INDENT.length);
    return {
      changes: { from: range.head, insert: " ".repeat(spaces) },
      range: EditorSelection.cursor(range.head + spaces),
    };
  });
  view.dispatch(state.update(transaction, { scrollIntoView: true, userEvent: "input" }));
  return true;
};

/** Pasa línea y columna del compilador (desde 1) a un desplazamiento en el
 *  documento. Se acota por si el texto cambió desde que se compiló. */
function toOffset(doc: Text, line: number, column: number): number {
  const lineInfo = doc.line(Math.min(Math.max(line, 1), doc.lines));
  return Math.min(lineInfo.from + Math.max(column - 1, 0), lineInfo.to);
}

function errorRange(doc: Text, error: CompileError): { from: number; to: number } {
  const from = toOffset(doc, error.line, error.column);
  const lineEnd = doc.lineAt(from).to;
  return { from, to: Math.min(from + Math.max(error.length, 1), lineEnd) };
}
