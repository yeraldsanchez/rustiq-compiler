/** Esquema del programa: las funciones, structs, enums y constantes del nivel
 *  superior. Sale del árbol de sintaxis del editor, así que está al día con
 *  cada tecla y no necesita compilar. */

import { syntaxTree } from "@codemirror/language";
import type { EditorState } from "@codemirror/state";
import type { SyntaxNode } from "@lezer/common";

export type OutlineKind = "func" | "struct" | "enum" | "const";

export interface OutlineItem {
  kind: OutlineKind;
  name: string;
  /** Cómo se declaró: `fn suma(a: i32) -> i32`, `struct Punto { x, y }`. */
  detail: string;
  line: number;
  from: number;
  to: number;
}

const ITEM_KIND: Record<string, OutlineKind> = {
  FunctionItem: "func",
  StructItem: "struct",
  EnumItem: "enum",
  ConstItem: "const",
};

const NAME_NODES = ["BoundIdentifier", "TypeIdentifier"];
const MAX_DETAIL = 80;

function nameNode(item: SyntaxNode): SyntaxNode | null {
  for (let child = item.firstChild; child; child = child.nextSibling) {
    if (NAME_NODES.includes(child.name)) return child;
  }
  return null;
}

function squeeze(text: string): string {
  const flat = text.replace(/\s+/g, " ").trim();
  return flat.length > MAX_DETAIL ? `${flat.slice(0, MAX_DETAIL - 1)}…` : flat;
}

/** Los nombres de un cuerpo `{ ... }`: campos de un struct o variantes. */
function memberNames(state: EditorState, item: SyntaxNode, kind: OutlineKind): string {
  const body = item.getChild(kind === "struct" ? "FieldDeclarationList" : "EnumVariantList");
  if (!body) return "";
  const members: string[] = [];
  body.cursor().iterate((node) => {
    if (node.name === "FieldIdentifier" || (kind === "enum" && node.name === "Identifier" && node.node.parent?.name === "EnumVariant")) {
      members.push(state.sliceDoc(node.from, node.to));
    }
  });
  return members.length ? ` { ${members.join(", ")} }` : " {}";
}

function detailOf(state: EditorState, item: SyntaxNode, kind: OutlineKind, name: string): string {
  switch (kind) {
    case "func": {
      const body = item.getChild("Block");
      return squeeze(state.sliceDoc(item.from, body ? body.from : item.to));
    }
    case "const": {
      const text = state.sliceDoc(item.from, item.to);
      return squeeze(text.split("=")[0]);
    }
    case "struct":
    case "enum":
      return squeeze(`${kind} ${name}${memberNames(state, item, kind)}`);
  }
}

export function outlineOf(state: EditorState): OutlineItem[] {
  const items: OutlineItem[] = [];
  const top = syntaxTree(state).topNode;
  for (let item = top.firstChild; item; item = item.nextSibling) {
    const kind = ITEM_KIND[item.name];
    const name = kind ? nameNode(item) : null;
    if (!kind || !name) continue;
    const text = state.sliceDoc(name.from, name.to);
    items.push({
      kind,
      name: text,
      detail: detailOf(state, item, kind, text),
      line: state.doc.lineAt(name.from).number,
      from: name.from,
      to: name.to,
    });
  }
  return items;
}
