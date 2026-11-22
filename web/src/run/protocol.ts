/** Mensajes entre el hilo principal y el Worker que ejecuta el programa. */

export interface RunRequest {
  wasm: ArrayBuffer;
}

export type WorkerMessage =
  | { kind: "print"; text: string }
  | { kind: "done" }
  | { kind: "trap"; message: string }
  | { kind: "limit" }
  | { kind: "error"; message: string };
