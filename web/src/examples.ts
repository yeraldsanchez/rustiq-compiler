/** Programas de ejemplo tomados de las pruebas del compilador. Vite los
 *  incrusta como texto al construir, así que no dependen del servidor. */

export interface Example {
  name: string;
  source: string;
}

export interface ExampleGroup {
  label: string;
  examples: Example[];
}

const valid = import.meta.glob<string>("../../tests/valid/*.rq", {
  query: "?raw",
  import: "default",
  eager: true,
});

const invalid = import.meta.glob<string>("../../tests/invalid/*.rq", {
  query: "?raw",
  import: "default",
  eager: true,
});

// Cabecera de las pruebas inválidas con el error esperado. Es para el runner,
// no para quien lee el ejemplo.
const EXPECTED_ERROR_HEADER = /^\/\/ ERROR .*\r?\n/;

function toExamples(files: Record<string, string>): Example[] {
  return Object.entries(files)
    .map(([path, source]) => ({
      name: path.slice(path.lastIndexOf("/") + 1),
      source: source.replace(EXPECTED_ERROR_HEADER, ""),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export const EXAMPLE_GROUPS: ExampleGroup[] = [
  { label: "Válidos", examples: toExamples(valid) },
  { label: "Con errores", examples: toExamples(invalid) },
];

export function findExample(name: string): Example | undefined {
  for (const group of EXAMPLE_GROUPS) {
    const found = group.examples.find((e) => e.name === name);
    if (found) return found;
  }
  return undefined;
}
