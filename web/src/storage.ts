/** Guarda el código en el navegador para no perderlo al recargar.
 *  El almacenamiento puede no existir (modo privado, bloqueado): en ese caso
 *  el editor funciona igual, solo que sin recordar nada. */

const SOURCE_KEY = "rustiq.source";

export function loadSource(): string | null {
  try {
    return localStorage.getItem(SOURCE_KEY);
  } catch {
    return null;
  }
}

export function saveSource(source: string): void {
  try {
    localStorage.setItem(SOURCE_KEY, source);
  } catch {
    // Sin almacenamiento no hay nada que hacer.
  }
}
