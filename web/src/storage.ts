/** Preferencias y código guardados en el navegador para no perderlos al
 *  recargar. El almacenamiento puede no existir (modo privado, bloqueado):
 *  en ese caso el editor funciona igual, solo que sin recordar nada. */

export const KEYS = {
  /** Versión anterior: un solo archivo. Se migra a `files`. */
  source: "rustiq.source",
  files: "rustiq.files",
  activeFile: "rustiq.activeFile",
  closedFiles: "rustiq.closedFiles",
  liveErrors: "rustiq.liveErrors",
  layout: "rustiq.layout",
} as const;

export function load(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function save(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Sin almacenamiento no hay nada que hacer.
  }
}

export function remove(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch {
    // Igual que arriba.
  }
}
