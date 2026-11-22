/** Editor de código: CodeMirror 6 con resaltado de Rust y los errores del
 *  compilador marcados en el texto. */

import { indentWithTab } from "@codemirror/commands";
import { rust } from "@codemirror/lang-rust";
import { indentUnit } from "@codemirror/language";
import { lintGutter, setDiagnostics, type Diagnostic } from "@codemirror/lint";
import { EditorSelection, Prec, type Text } from "@codemirror/state";
import { EditorView, keymap } from "@codemirror/view";
import { basicSetup } from "codemirror";

import { PHASE_LABEL, type CompileError } from "../types";
import { rustiqTheme } from "./theme";

// Sangría de 4 espacios, como en Rust.
const INDENT = "    ";

export interface EditorCallbacks {
  onChange(source: string): void;
  onCursor(line: number, column: number): void;
  onCompile(): void;
  onRun(): void;
}

export interface Editor {
  getSource(): string;
  setSource(source: string): void;
  showErrors(errors: CompileError[]): void;
  goTo(line: number, column: number): void;
}

export function createEditor(parent: HTMLElement, initial: string, callbacks: EditorCallbacks): Editor {
  const shortcuts = Prec.highest(
    keymap.of([
      { key: "Mod-Enter", run: () => (callbacks.onRun(), true) },
      { key: "Mod-b", run: () => (callbacks.onCompile(), true) },
      // El código se guarda solo; esto evita el diálogo de guardar del navegador.
      { key: "Mod-s", run: () => true },
      // Tab indenta en vez de mover el foco. Para salir del editor con el
      // teclado: Esc y luego Tab (comportamiento de CodeMirror).
      indentWithTab,
    ]),
  );

  const view = new EditorView({
    parent,
    doc: initial,
    extensions: [
      basicSetup,
      rust(),
      indentUnit.of(INDENT),
      lintGutter(),
      rustiqTheme,
      shortcuts,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) callbacks.onChange(update.state.doc.toString());
        if (update.docChanged || update.selectionSet) {
          const head = update.state.selection.main.head;
          const line = update.state.doc.lineAt(head);
          callbacks.onCursor(line.number, head - line.from + 1);
        }
      }),
    ],
  });

  return {
    getSource: () => view.state.doc.toString(),

    setSource(source) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: source },
        selection: EditorSelection.cursor(0),
        scrollIntoView: true,
      });
    },

    showErrors(errors) {
      const diagnostics = errors.map((e) => toDiagnostic(view.state.doc, e));
      view.dispatch(setDiagnostics(view.state, diagnostics));
    },

    goTo(line, column) {
      const pos = toOffset(view.state.doc, line, column);
      view.dispatch({ selection: EditorSelection.cursor(pos), scrollIntoView: true });
      view.focus();
    },
  };
}

/** Pasa línea y columna del compilador (desde 1) a un desplazamiento en el
 *  documento. Se acota por si el texto cambió desde que se compiló. */
function toOffset(doc: Text, line: number, column: number): number {
  const lineInfo = doc.line(Math.min(Math.max(line, 1), doc.lines));
  return Math.min(lineInfo.from + Math.max(column - 1, 0), lineInfo.to);
}

function toDiagnostic(doc: Text, error: CompileError): Diagnostic {
  const from = toOffset(doc, error.line, error.column);
  const lineEnd = doc.lineAt(from).to;
  return {
    from,
    to: Math.min(from + Math.max(error.length, 1), lineEnd),
    severity: "error",
    message: error.message,
    source: `${PHASE_LABEL[error.phase]} · ${error.code}`,
  };
}
