/** Preferencias y código guardados en el navegador para no perderlos al
 *  recargar. El almacenamiento puede no existir (modo privado, bloqueado):
 *  en ese caso el editor funciona igual, solo que sin recordar nada. */

export const KEYS = {
  source: "rustiq.source",
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
