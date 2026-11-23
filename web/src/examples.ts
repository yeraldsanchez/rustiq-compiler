/** Programas de ejemplo: los de web/examples/ y los de las pruebas del
 *  compilador. Vite los incrusta como texto al construir, así que no
 *  dependen del servidor. */

export interface Example {
  /** Nombre del archivo: `uso_despues_de_mover.rq`. */
  name: string;
  /** Para mostrar: "Uso después de mover". */
  title: string;
  /** Una línea sobre qué muestra el ejemplo. */
  description: string;
  /** Código del error que provoca, en los ejemplos con errores. */
  errorCode?: string;
  source: string;
}

export interface ExampleGroup {
  label: string;
  examples: Example[];
}

const starters = import.meta.glob<string>("../examples/*.rq", {
  query: "?raw",
  import: "default",
  eager: true,
});

const valid = import.meta.glob<string>("../../tests/valid/*.rq", {
  query: "?raw",
  import: "default",
  eager: true,
});

const invalid = import.meta.glob<string>("../../tests/invalid/*.rq", {
  query: "?raw",
  import: "default",
  eager: true,
});

// Cabecera de las pruebas inválidas con el error esperado. Es para el runner,
// no para quien lee el ejemplo, así que se quita del código.
const EXPECTED_ERROR_HEADER = /^\/\/ ERROR \S+ (E_[A-Z_]+).*\r?\n/;
// Prefijos de los nombres de las pruebas que no aportan al título: a_, c_, test_b3_.
const NAME_PREFIX = /^(?:test_[a-z]\d+_|[abc]_)/;
const LEADING_COMMENT = /^\/\/\s*(.+)/;

// Qué significa cada error, en palabras de quien aprende.
const ERROR_DESCRIPTION: Record<string, string> = {
  E_INVALID_CHAR: "Carácter que el lenguaje no reconoce",
  E_UNTERMINATED_STRING: "Cadena sin cerrar",
  E_UNTERMINATED_COMMENT: "Comentario de bloque sin cerrar",
  E_INVALID_ESCAPE: "Secuencia de escape no válida",
  E_SYNTAX: "Error de sintaxis",
  E_UNDECLARED: "Nombre que no está declarado",
  E_REDECLARED: "Nombre declarado dos veces",
  E_TYPE_MISMATCH: "Tipos que no coinciden",
  E_UNKNOWN_TYPE: "Tipo que no existe",
  E_CANNOT_INFER: "No se puede inferir el tipo",
  E_BAD_OPERAND: "Operador con un tipo que no acepta",
  E_INT_OUT_OF_RANGE: "Entero que no cabe en i32",
  E_ARG_COUNT: "Número de argumentos incorrecto",
  E_NOT_CALLABLE: "Se llama algo que no es función",
  E_UNKNOWN_FIELD: "Campo que el struct no tiene",
  E_MISSING_FIELD: "Falta un campo del struct",
  E_UNKNOWN_VARIANT: "Variante que el enum no tiene",
  E_NOT_EXHAUSTIVE: "match que no cubre todos los casos",
  E_BAD_PATTERN: "Patrón que no corresponde al valor",
  E_BAD_INDEX: "Índice no válido",
  E_BAD_RETURN: "return que no corresponde a la función",
  E_BREAK_OUTSIDE_LOOP: "break o continue fuera de un ciclo",
  E_BAD_MAIN: "Problema con la función main",
  E_ASSIGN_IMMUTABLE: "Asignar a algo que no es mut",
  E_UNINITIALIZED: "Uso de una variable sin inicializar",
  E_USE_AFTER_MOVE: "Uso de un valor después de moverlo",
  E_MOVE_WHILE_BORROWED: "Mover un valor que está prestado",
  E_MOVE_OUT_OF_PLACE: "Mover desde una referencia o un campo",
  E_BORROW_CONFLICT: "Préstamos en conflicto",
  E_BORROW_MUT_IMMUTABLE: "&mut de algo que no es mut",
  E_ASSIGN_WHILE_BORROWED: "Asignar a algo que está prestado",
  E_RETURN_LOCAL_REF: "Devolver una referencia a una variable local",
  E_DANGLING_REF: "Referencia que sobrevive a su valor",
};

/** `c_mover_campo_propio.rq` → "Mover campo propio". */
function titleOf(name: string): string {
  const words = name.replace(/\.rq$/, "").replace(NAME_PREFIX, "").replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function toExample(path: string, raw: string): Example {
  const name = path.slice(path.lastIndexOf("/") + 1);
  const header = EXPECTED_ERROR_HEADER.exec(raw);
  const source = header ? raw.slice(header[0].length) : raw;
  const errorCode = header?.[1];
  const comment = LEADING_COMMENT.exec(source)?.[1].trim();
  const description = errorCode ? (ERROR_DESCRIPTION[errorCode] ?? errorCode) : (comment ?? "");
  return { name, title: titleOf(name), description, errorCode, source };
}

function toExamples(files: Record<string, string>): Example[] {
  return Object.entries(files)
    .map(([path, source]) => toExample(path, source))
    .sort((a, b) => a.title.localeCompare(b.title, "es"));
}

export const EXAMPLE_GROUPS: ExampleGroup[] = [
  { label: "Para empezar", examples: toExamples(starters) },
  { label: "Programas válidos", examples: toExamples(valid) },
  { label: "Con errores", examples: toExamples(invalid) },
];

export function findExample(name: string): Example | undefined {
  for (const group of EXAMPLE_GROUPS) {
    const found = group.examples.find((e) => e.name === name);
    if (found) return found;
  }
  return undefined;
}
