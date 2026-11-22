/** Forma JSON de las respuestas de `POST /compile` (contrato 6 del plan). */

export type Phase = "lexico" | "sintactico" | "semantico" | "backend";

export interface CompileError {
  phase: Phase;
  code: string;
  message: string;
  line: number;
  column: number;
  length: number;
}

export interface CompileResponse {
  ok: boolean;
  errors: CompileError[];
  wat: string | null;
  wasm_base64: string | null;
}

/** Nombre de cada fase tal como se muestra en la interfaz. */
export const PHASE_LABEL: Record<Phase, string> = {
  lexico: "léxico",
  sintactico: "sintáctico",
  semantico: "semántico",
  backend: "backend",
};
