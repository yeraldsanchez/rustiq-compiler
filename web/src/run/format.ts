/** Formato de valores y mensajes de la ejecución. Debe coincidir con
 *  rustiq/host.py, que es el host de las pruebas. */

/** Python escribe `3.0` donde JavaScript escribe `3`. */
export function formatF64(value: number): string {
  if (Number.isNaN(value)) return "nan";
  if (!Number.isFinite(value)) return value > 0 ? "inf" : "-inf";
  if (Number.isInteger(value) && Math.abs(value) < 1e16) return value.toFixed(1);
  return String(value);
}

// Mensajes de los navegadores (V8 y SpiderMonkey) para cada trap de Wasm.
const TRAP_MESSAGES: [RegExp, string][] = [
  [/unreachable/i, "se llegó a una instrucción inalcanzable (unreachable)"],
  [/divi(de|sion) by zero/i, "división entre cero"],
  [/remainder by zero/i, "residuo entre cero"],
  [/integer overflow/i, "desbordamiento de entero"],
  [/out of bounds/i, "acceso a memoria fuera de rango"],
  [/stack|recursion/i, "desbordamiento de pila (recursión demasiado profunda)"],
];

export function describeTrap(message: string): string {
  const match = TRAP_MESSAGES.find(([pattern]) => pattern.test(message));
  return match ? match[1] : message;
}
