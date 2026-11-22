/** Tema de CodeMirror con los tokens de color de styles.css, para que el
 *  editor, la vista del WAT y el resto de la interfaz cambien juntos. */

import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { EditorView } from "@codemirror/view";
import { tags as t } from "@lezer/highlight";

const chrome = EditorView.theme(
  {
    "&": {
      height: "100%",
      color: "var(--text-2)",
      backgroundColor: "var(--tile)",
      fontSize: "13px",
    },
    "&.cm-focused": { outline: "none" },
    ".cm-scroller": {
      fontFamily: "var(--font-mono)",
      lineHeight: "1.65",
    },
    ".cm-content": { padding: "12px 0", caretColor: "var(--accent)" },
    ".cm-cursor, .cm-dropCursor": { borderLeft: "2px solid var(--accent)" },
    ".cm-gutters": {
      backgroundColor: "var(--tile)",
      color: "var(--muted)",
      border: "none",
    },
    ".cm-lineNumbers .cm-gutterElement": { minWidth: "36px", padding: "0 12px 0 0" },
    ".cm-activeLine": { backgroundColor: "var(--hover)" },
    ".cm-activeLineGutter": { backgroundColor: "transparent", color: "var(--text)" },
    "&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection": {
      backgroundColor: "rgba(242, 107, 29, 0.25) !important",
    },
    ".cm-matchingBracket": {
      backgroundColor: "transparent",
      outline: "1px solid var(--line-strong)",
    },
    ".cm-gutter-lint": { width: "3px" },
    ".cm-gutter-lint .cm-gutterElement": { padding: "0" },
    ".cm-lintRange-error": {
      backgroundImage: "none",
      textDecoration: "underline wavy var(--error)",
      textDecorationSkipInk: "none",
      textUnderlineOffset: "4px",
    },
    ".cm-tooltip": {
      backgroundColor: "var(--tile-2)",
      color: "var(--text)",
      border: "1px solid var(--line-strong)",
      boxShadow: "var(--press)",
    },
    ".cm-diagnostic": { padding: "6px 10px", fontFamily: "var(--font-ui)" },
    ".cm-diagnostic-error": { borderLeft: "3px solid var(--error)" },
    ".cm-diagnosticSource": {
      marginTop: "2px",
      color: "var(--muted)",
      fontFamily: "var(--font-mono)",
      fontSize: "11.5px",
      opacity: "1",
    },
    ".cm-tooltip.cm-tooltip-autocomplete > ul": {
      fontFamily: "var(--font-mono)",
      fontSize: "12.5px",
      maxHeight: "16em",
    },
    ".cm-tooltip.cm-tooltip-autocomplete > ul > li": { padding: "2px 10px 2px 6px" },
    ".cm-tooltip-autocomplete > ul > li[aria-selected]": {
      backgroundColor: "var(--accent)",
      color: "var(--accent-ink)",
    },
    ".cm-completionIcon": { width: "1.4em", opacity: "0.7" },
    ".cm-completionDetail": { marginLeft: "1em", fontStyle: "normal", color: "var(--muted)" },
    "li[aria-selected] .cm-completionDetail": { color: "inherit" },
    ".cm-completionMatchedText": { textDecoration: "none", fontWeight: "700" },
    ".cm-panels": { backgroundColor: "var(--tile-2)", color: "var(--text)" },
  },
  { dark: true },
);

const rustHighlight = HighlightStyle.define([
  { tag: [t.keyword, t.definitionKeyword, t.controlKeyword, t.modifier, t.operatorKeyword], color: "var(--kw)" },
  { tag: [t.typeName, t.standard(t.typeName)], color: "var(--ty)" },
  { tag: [t.function(t.variableName), t.function(t.definition(t.variableName))], color: "var(--fn)" },
  { tag: [t.integer, t.float, t.bool], color: "var(--num)" },
  { tag: [t.string, t.character], color: "var(--ok)" },
  { tag: [t.lineComment, t.blockComment], color: "var(--muted)", fontStyle: "italic" },
]);

// En WAT casi todo es instrucción (`keyword`), así que va en el color base y
// se destacan los nombres `$x`, los tipos y los números.
const watHighlight = HighlightStyle.define([
  { tag: t.keyword, color: "var(--kw)" },
  { tag: t.typeName, color: "var(--ty)" },
  { tag: t.variableName, color: "var(--fn)" },
  { tag: t.number, color: "var(--num)" },
  { tag: t.string, color: "var(--ok)" },
  { tag: [t.lineComment, t.blockComment], color: "var(--muted)", fontStyle: "italic" },
  { tag: t.paren, color: "var(--muted)" },
]);

export const editorChrome = chrome;
export const rustHighlighting = syntaxHighlighting(rustHighlight);
export const watHighlighting = syntaxHighlighting(watHighlight);
