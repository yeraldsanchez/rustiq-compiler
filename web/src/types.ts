/** Forma JSON de las respuestas de `POST /compile` (`server/app.py`). */

export type Phase = "lexico" | "sintactico" | "semantico" | "backend";

export interface CompileError {
  phase: Phase;
  code: string;
  message: string;
  line: number;
  column: number;
  length: number;
}

export type SymbolKind = "local" | "param" | "const" | "func" | "host" | "struct" | "enum" | "variant";

/** Qué es un identificador del programa (rustiq/symbols.py). */
export interface SymbolHint {
  line: number;
  column: number;
  length: number;
  name: string;
  kind: SymbolKind;
  /** El tipo, o la declaración completa si es función, struct, enum o
   *  variante. Null si hubo un error. */
  type: string | null;
  mutable: boolean;
  declaration: boolean;
  /** Igual en la declaración y en todos los usos del mismo nombre. */
  id: string;
}

export interface CompileResponse {
  ok: boolean;
  errors: CompileError[];
  wat: string | null;
  wasm_base64: string | null;
  /** Puede faltar si el servidor es una versión anterior. */
  symbols?: SymbolHint[];
}

/** Nombre de cada fase tal como se muestra en la interfaz. */
export const PHASE_LABEL: Record<Phase, string> = {
  lexico: "léxico",
  sintactico: "sintáctico",
  semantico: "semántico",
  backend: "backend",
};
