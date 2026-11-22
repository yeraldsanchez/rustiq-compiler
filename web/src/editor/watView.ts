/** Vista de solo lectura del WAT generado, con resaltado, números de línea,
 *  plegado y búsqueda (Ctrl+F). */

import { foldGutter, foldKeymap } from "@codemirror/language";
import { wast } from "@codemirror/lang-wast";
import { searchKeymap, highlightSelectionMatches } from "@codemirror/search";
import { EditorState } from "@codemirror/state";
import { EditorView, keymap, lineNumbers } from "@codemirror/view";

import { editorChrome, watHighlighting } from "./theme";

export interface WatView {
  setText(text: string): void;
}

export function createWatView(parent: HTMLElement): WatView {
  const view = new EditorView({
    parent,
    extensions: [
      EditorState.readOnly.of(true),
      lineNumbers(),
      foldGutter(),
      highlightSelectionMatches(),
      keymap.of([...searchKeymap, ...foldKeymap]),
      wast(),
      editorChrome,
      watHighlighting,
    ],
  });

  return {
    setText(text) {
      view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: text } });
      view.scrollDOM.scrollTop = 0;
    },
  };
}
