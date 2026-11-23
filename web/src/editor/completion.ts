/** Autocompletado de RustiQ: palabras clave de la gramática, tipos, las
 *  funciones del host y plantillas para las construcciones comunes. Además
 *  sugiere los identificadores del programa (variables, funciones, structs),
 *  tomados del árbol de sintaxis para no sugerir palabras de comentarios. */

import {
  completeFromList,
  ifNotIn,
  snippetCompletion,
  type Completion,
  type CompletionContext,
  type CompletionResult,
} from "@codemirror/autocomplete";
import { rustLanguage } from "@codemirror/lang-rust";
import { syntaxTree } from "@codemirror/language";

// Deben coincidir con grammar/RustiQ.g4 y rustiq/builtins.py.
export const KEYWORDS = [
  "fn", "struct", "enum", "const", "let", "mut", "return", "break",
  "continue", "while", "loop", "if", "else", "match", "true", "false",
];
export const TYPES = ["i32", "f64", "bool", "char", "String"];
export const HOST_FUNCTIONS: [name: string, param: string][] = [
  ["print_i32", "i32"],
  ["print_f64", "f64"],
  ["print_bool", "bool"],
  ["print_char", "char"],
  ["print_str", "String"],
];

const SNIPPETS: Completion[] = [
  snippetCompletion("fn ${nombre}(${}) {\n\t${}\n}", { label: "fn", detail: "función", type: "keyword" }),
  snippetCompletion("fn main() {\n\t${}\n}", { label: "main", detail: "punto de entrada", type: "keyword" }),
  snippetCompletion("let ${nombre} = ${valor};", { label: "let", detail: "variable", type: "keyword" }),
  snippetCompletion("if ${condicion} {\n\t${}\n}", { label: "if", detail: "condicional", type: "keyword" }),
  snippetCompletion("while ${condicion} {\n\t${}\n}", { label: "while", detail: "ciclo", type: "keyword" }),
  snippetCompletion("loop {\n\t${}\n}", { label: "loop", detail: "ciclo infinito", type: "keyword" }),
  snippetCompletion("match ${valor} {\n\t${patron} => ${},\n\t_ => ${},\n}", { label: "match", detail: "coincidencia", type: "keyword" }),
  snippetCompletion("struct ${Nombre} {\n\t${campo}: ${i32},\n}", { label: "struct", detail: "estructura", type: "keyword" }),
  snippetCompletion("enum ${Nombre} {\n\t${Variante},\n}", { label: "enum", detail: "enumeración", type: "keyword" }),
];

const snippetLabels = new Set(SNIPPETS.map((s) => s.label));

// Lo del lenguaje va antes que los identificadores del programa.
const LANGUAGE_BOOST = 1;

const OPTIONS: Completion[] = [
  ...SNIPPETS,
  ...KEYWORDS.filter((k) => !snippetLabels.has(k)).map((label) => ({ label, type: "keyword" })),
  ...TYPES.map((label) => ({ label, type: "type" })),
  ...HOST_FUNCTIONS.map(([name, param]) =>
    snippetCompletion(`${name}(\${})`, { label: name, detail: `(${param})`, type: "function" }),
  ),
].map((option) => ({ ...option, boost: LANGUAGE_BOOST }));

const LANGUAGE_LABELS = new Set(OPTIONS.map((o) => o.label));

// Nodos de @lezer/rust que nombran algo declarado en el programa.
const IDENTIFIER_NODES: Record<string, Completion["type"]> = {
  Identifier: "variable",
  BoundIdentifier: "variable",
  TypeIdentifier: "class",
  FieldIdentifier: "property",
};

const WORD = /[A-Za-z_][A-Za-z0-9_]*/;

function programIdentifiers(context: CompletionContext): CompletionResult | null {
  const word = context.matchBefore(WORD);
  if (!word || (word.from === word.to && !context.explicit)) return null;

  const found = new Map<string, Completion["type"]>();
  syntaxTree(context.state).iterate({
    enter(node) {
      const type = IDENTIFIER_NODES[node.name];
      // Se salta la palabra que se está escribiendo.
      if (!type || node.to === word.to) return;
      const name = context.state.sliceDoc(node.from, node.to);
      if (!LANGUAGE_LABELS.has(name) && !found.has(name)) found.set(name, type);
    },
  });

  return {
    from: word.from,
    options: [...found].map(([label, type]) => ({ label, type })),
    validFor: /^[A-Za-z0-9_]*$/,
  };
}

// Dentro de comentarios y cadenas no se sugiere nada.
const NOT_IN = ["LineComment", "BlockComment", "String", "Char"];

export const rustiqCompletion = [
  rustLanguage.data.of({ autocomplete: ifNotIn(NOT_IN, completeFromList(OPTIONS)) }),
  rustLanguage.data.of({ autocomplete: ifNotIn(NOT_IN, programIdentifiers) }),
];
