import type { CompileResponse } from "./types";

const COMPILE_URL = "/compile";

/** El servidor no respondió o respondió algo que no es una compilación. */
export class ConnectionError extends Error {}

export async function compileSource(source: string): Promise<CompileResponse> {
  let response: Response;
  try {
    response = await fetch(COMPILE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source }),
    });
  } catch {
    throw new ConnectionError(
      `El servidor no respondió en ${COMPILE_URL}. Revisa que uvicorn esté corriendo.`,
    );
  }
  if (response.status === 422) {
    throw new ConnectionError("El servidor rechazó el programa: es demasiado largo.");
  }
  if (!response.ok) {
    throw new ConnectionError(`El servidor respondió con el código ${response.status}.`);
  }
  return (await response.json()) as CompileResponse;
}

export function decodeBase64(data: string): Uint8Array<ArrayBuffer> {
  const binary = atob(data);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}
