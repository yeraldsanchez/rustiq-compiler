import type { CompileResponse } from "./types";

const COMPILE_URL = "/compile";
const HTTP_TOO_LARGE = 422;
const HTTP_BUSY = 503;

/** El servidor no respondió o respondió algo que no es una compilación. */
export class ConnectionError extends Error {}

/** El servidor está ocupado (503): conviene reintentar en unos segundos. */
export class ServerBusyError extends ConnectionError {}

/** Una compilación más nueva reemplazó a esta antes de que respondiera. */
export class CompileCancelledError extends Error {}

// La compilación en vuelo. Al mandar otra se cancela: solo importa la última,
// y así cada pestaña ocupa a lo más un lugar en el servidor.
let inFlight: AbortController | null = null;

export async function compileSource(source: string): Promise<CompileResponse> {
  inFlight?.abort();
  const controller = new AbortController();
  inFlight = controller;
  try {
    return await request(source, controller.signal);
  } finally {
    if (inFlight === controller) inFlight = null;
  }
}

async function request(source: string, signal: AbortSignal): Promise<CompileResponse> {
  let response: Response;
  try {
    response = await fetch(COMPILE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source }),
      signal,
    });
  } catch {
    if (signal.aborted) throw new CompileCancelledError();
    throw new ConnectionError(
      `El servidor no respondió en ${COMPILE_URL}. Revisa que uvicorn esté corriendo.`,
    );
  }
  if (response.status === HTTP_TOO_LARGE) {
    throw new ConnectionError("El servidor rechazó el programa: es demasiado largo.");
  }
  if (response.status === HTTP_BUSY) {
    throw new ServerBusyError("El servidor está ocupado, intenta de nuevo en unos segundos.");
  }
  if (!response.ok) {
    throw new ConnectionError(`El servidor respondió con el código ${response.status}.`);
  }
  try {
    return (await response.json()) as CompileResponse;
  } catch {
    if (signal.aborted) throw new CompileCancelledError();
    throw new ConnectionError("El servidor respondió algo que no es una compilación.");
  }
}

export function decodeBase64(data: string): Uint8Array<ArrayBuffer> {
  const binary = atob(data);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}
