/** Ejecuta un módulo compilado fuera del hilo de la interfaz, así un ciclo
 *  infinito no congela la página y se puede detener con `terminate()`.
 *  Implementa las funciones `env.print_*` (ABI en docs/memoria.md). */

import { describeTrap, formatF64 } from "./format";
import type { RunRequest, WorkerMessage } from "./protocol";

// Corta programas que imprimen sin parar antes de saturar la interfaz.
const MAX_LINES = 10_000;
// Un String en memoria: 4 bytes de largo (little endian) y luego los bytes UTF-8.
const STR_LEN_BYTES = 4;

class OutputLimit extends Error {}

const decoder = new TextDecoder();
let memory: WebAssembly.Memory | null = null;
let lines = 0;

function post(message: WorkerMessage): void {
  self.postMessage(message);
}

function print(text: string): void {
  lines += 1;
  if (lines > MAX_LINES) throw new OutputLimit();
  post({ kind: "print", text });
}

function readString(ptr: number): string {
  if (!memory) throw new Error("El módulo no exporta su memoria.");
  const length = new DataView(memory.buffer).getUint32(ptr, true);
  return decoder.decode(new Uint8Array(memory.buffer, ptr + STR_LEN_BYTES, length));
}

const env = {
  print_i32: (n: number) => print(String(n)),
  print_f64: (x: number) => print(formatF64(x)),
  print_bool: (b: number) => print(b ? "true" : "false"),
  print_char: (c: number) => print(String.fromCodePoint(c)),
  print_str: (ptr: number) => print(readString(ptr)),
};

self.onmessage = async (event: MessageEvent<RunRequest>) => {
  try {
    const { instance } = await WebAssembly.instantiate(event.data.wasm, { env });
    const exports = instance.exports;
    memory = (exports.memory as WebAssembly.Memory | undefined) ?? null;
    const entry = (exports._start ?? exports.main) as (() => void) | undefined;
    if (!entry) throw new Error("El módulo no exporta `main`.");
    entry();
    post({ kind: "done" });
  } catch (error) {
    if (error instanceof OutputLimit) post({ kind: "limit" });
    else if (error instanceof WebAssembly.RuntimeError) post({ kind: "trap", message: describeTrap(error.message) });
    else post({ kind: "error", message: error instanceof Error ? error.message : String(error) });
  }
};
