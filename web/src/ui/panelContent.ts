/** Qué muestra cada lista del panel lateral y de los atajos: convierte los
 *  archivos, el esquema y los ejemplos en grupos de `ListView`. Solo arma
 *  datos; las acciones llegan desde main.ts. */

import type { OutlineItem, OutlineKind } from "../editor/outline";
import type { Example, ExampleGroup } from "../examples";
import type { SourceFile } from "../files";
import type { ListGroup, ListItem } from "./listView";

export interface FileActions {
  select(id: string): void;
  close(id: string): void;
  download(): void;
  rename(): void;
}

export function fileGroups(files: readonly SourceFile[], active: SourceFile | null, actions: FileActions): ListGroup[] {
  const open: ListGroup = {
    label: "Abiertos",
    items: files.map((file) => ({
      title: file.name,
      current: file.id === active?.id,
      actions: [{ label: "×", title: `Cerrar ${file.name}`, run: () => actions.close(file.id) }],
      onSelect: () => actions.select(file.id),
    })),
  };
  if (!active) return [open];
  return [
    open,
    {
      label: "Archivo activo",
      items: [
        { title: `Descargar ${active.name}`, onSelect: actions.download },
        { title: "Renombrar", meta: "F2 en la pestaña", onSelect: actions.rename },
      ],
    },
  ];
}

const OUTLINE_GROUPS: [OutlineKind, string, ListItem["badge"]][] = [
  ["func", "Funciones", { text: "ƒ", tone: "fn" }],
  ["struct", "Structs", { text: "S", tone: "type" }],
  ["enum", "Enums", { text: "E", tone: "enum" }],
  ["const", "Constantes", { text: "C", tone: "const" }],
];

export function outlineGroups(items: OutlineItem[], select: (item: OutlineItem) => void): ListGroup[] {
  return OUTLINE_GROUPS.map(([kind, label, badge]) => ({
    label,
    items: items
      .filter((item) => item.kind === kind)
      .map((item) => ({
        title: item.name,
        detail: item.detail,
        meta: String(item.line),
        badge,
        keywords: item.detail,
        onSelect: () => select(item),
      })),
  }));
}

export function exampleGroups(
  groups: ExampleGroup[],
  activeName: string | null,
  open: (example: Example) => void,
): ListGroup[] {
  return groups
    .filter((group) => group.examples.length)
    .map((group) => ({
      label: group.label,
      items: group.examples.map((example) => ({
        title: example.title,
        detail: example.description || undefined,
        meta: example.errorCode,
        metaTone: example.errorCode ? "error" : undefined,
        keywords: example.name,
        current: example.name === activeName,
        onSelect: () => open(example),
      })),
    }));
}

const SHORTCUTS: [string, [title: string, keys: string][]][] = [
  [
    "Programa",
    [
      ["Compilar", "Ctrl+B"],
      ["Compilar y ejecutar", "Ctrl+Enter"],
    ],
  ],
  [
    "Archivos",
    [
      ["Archivo nuevo", "Alt+N"],
      ["Abrir desde el disco", "Ctrl+O"],
      ["Panel de archivos", "Ctrl+Shift+E"],
      ["Renombrar la pestaña enfocada", "F2"],
    ],
  ],
  [
    "Código",
    [
      ["Esquema del programa", "Ctrl+Shift+O"],
      ["Ir a la definición", "F12 · Ctrl+clic"],
      ["Ver referencias", "Shift+F12"],
      ["Renombrar símbolo", "F2"],
      ["Buscar y reemplazar", "Ctrl+F"],
      ["Aceptar sugerencia", "Tab"],
    ],
  ],
];

export function shortcutGroups(): ListGroup[] {
  return SHORTCUTS.map(([label, rows]) => ({
    label,
    items: rows.map(([title, keys]) => ({ title, meta: keys, onSelect: () => {} })),
  }));
}
