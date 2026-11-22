/** Formato de valores y mensajes de la ejecución. Debe coincidir con
 *  rustiq/host.py, que es el host de las pruebas. */

// Python usa notación científica fuera de 1e-4 <= |x| < 1e16 (JavaScript, fuera de 1e-7 <= |x| < 1e21).
const MIN_FIXED_EXPONENT = -4;
const MAX_FIXED_EXPONENT = 16;
const EXPONENT_DIGITS = 2;

/** Igual que `repr(float)` de Python: `3.0`, `0.5`, `1e-05`, `1.5e+16`, `inf`, `nan`.
 *  Los dígitos son los mismos (el más corto que identifica el número);
 *  cambia dónde va el punto y cómo se escribe el exponente. */
export function formatF64(value: number): string {
  if (Number.isNaN(value)) return "nan";
  if (!Number.isFinite(value)) return value > 0 ? "inf" : "-inf";
  if (value === 0) return Object.is(value, -0) ? "-0.0" : "0.0";
  const [mantissa, exponentText] = value.toExponential().split("e");
  const exponent = Number(exponentText);
  if (exponent >= MIN_FIXED_EXPONENT && exponent < MAX_FIXED_EXPONENT) {
    const fixed = String(value);
    return fixed.includes(".") ? fixed : `${fixed}.0`;
  }
  const sign = exponent < 0 ? "-" : "+";
  return `${mantissa}e${sign}${String(Math.abs(exponent)).padStart(EXPONENT_DIGITS, "0")}`;
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
