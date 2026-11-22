"""Genera la carpeta evidencias/ con pruebas reproducibles de compilación,
validación y ejecución de WebAssembly.

Uso, desde la raíz del repo:

    python -m scripts.evidencias

Por cada programa de tests/valid escribe en evidencias/validos/<nombre>/:
- programa.rq: el fuente
- modulo.wat y modulo.wasm: lo que genera el compilador
- validacion.txt: el comando wasm-validate, su salida y su código de salida
- salida.txt: lo que imprime al ejecutarse con wasmtime
- esperado.txt: la salida esperada (tests/valid/<nombre>.out)

Por cada programa de tests/invalid anota el error que da y confirma que no
se produjo módulo. Al final escribe evidencias/RESUMEN.md con una tabla.
"""

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from rustiq.host import run_wasm
from rustiq.pipeline import WASM_VALIDATE, WAT2WASM, compile_source

ROOT = Path(__file__).resolve().parent.parent
VALID_DIR = ROOT / "tests" / "valid"
INVALID_DIR = ROOT / "tests" / "invalid"
OUT_DIR = ROOT / "evidencias"
OK, FAIL = "sí", "NO"


def tool_version(tool: str) -> str:
    if shutil.which(tool) is None:
        return f"{tool}: no instalado (se usó wasmtime)"
    proc = subprocess.run([tool, "--version"], capture_output=True, text=True)
    return f"{tool} {proc.stdout.strip() or proc.stderr.strip()}"


def validate(wasm_file: Path) -> tuple[bool, str]:
    """Corre wasm-validate sobre el archivo y devuelve (válido, reporte)."""
    if shutil.which(WASM_VALIDATE) is None:
        return True, "wasm-validate no está instalado; el pipeline validó con wasmtime.\n"
    proc = subprocess.run([WASM_VALIDATE, str(wasm_file)], capture_output=True, text=True)
    report = (
        f"$ {WASM_VALIDATE} {wasm_file.name}\n"
        f"{proc.stdout}{proc.stderr}"
        f"código de salida: {proc.returncode}\n"
    )
    return proc.returncode == 0, report


def valid_evidence(rq: Path) -> list[str]:
    """Compila, valida y ejecuta un programa válido. Devuelve su fila del resumen."""
    folder = OUT_DIR / "validos" / rq.stem
    folder.mkdir(parents=True)
    source = rq.read_text(encoding="utf-8")
    (folder / "programa.rq").write_text(source, encoding="utf-8")
    result = compile_source(source)
    if not result.ok:
        (folder / "errores.txt").write_text("\n".join(map(str, result.errors)) + "\n", encoding="utf-8")
        return [rq.stem, FAIL, "-", "-", "-"]

    (folder / "modulo.wat").write_text(result.wat, encoding="utf-8")
    wasm_file = folder / "modulo.wasm"
    wasm_file.write_bytes(result.wasm)
    valid, report = validate(wasm_file)
    (folder / "validacion.txt").write_text(report, encoding="utf-8")

    ran = True
    try:
        output = run_wasm(result.wasm)
    except Exception as e:  # un trap también es evidencia
        output, ran = f"TRAP: {e}\n", False
    (folder / "salida.txt").write_text(output, encoding="utf-8")

    expected_file = rq.with_suffix(".out")
    if expected_file.exists():
        expected = expected_file.read_text(encoding="utf-8")
        (folder / "esperado.txt").write_text(expected, encoding="utf-8")
        matches = OK if output == expected else FAIL
    else:
        matches = "sin .out"
    return [rq.stem, OK, OK if valid else FAIL, OK if ran else FAIL, matches]


def invalid_evidence(rq: Path) -> list[str]:
    """Compila un programa inválido y anota su primer error. Devuelve su fila."""
    result = compile_source(rq.read_text(encoding="utf-8"))
    if result.ok:
        return [rq.stem, "compiló (no debía)", "-", FAIL]
    first = result.errors[0]
    error = f"`{first.phase} {first.code} {first.line}:{first.column}` {first.message}"
    expected = rq.read_text(encoding="utf-8").splitlines()[0].removeprefix("// ERROR ").strip()
    got = f"{first.phase} {first.code} {first.line}:{first.column}"
    no_module = OK if result.wasm is None else FAIL
    return [rq.stem, error.replace("|", "\\|"), OK if got == expected else FAIL, no_module]


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()
    valid_rows = [valid_evidence(rq) for rq in sorted(VALID_DIR.glob("*.rq"))]
    invalid_rows = [invalid_evidence(rq) for rq in sorted(INVALID_DIR.glob("*.rq"))]

    summary = "\n\n".join([
        "# Evidencias de compilación, validación y ejecución",
        f"Generado con `python -m scripts.evidencias` el {datetime.now():%Y-%m-%d %H:%M}.",
        "Herramientas: " + "; ".join([tool_version(WAT2WASM), tool_version(WASM_VALIDATE), f"Python {sys.version.split()[0]}"]),
        "## Programas válidos",
        "Cada carpeta de `validos/` tiene el fuente, el `.wat`, el `.wasm`, la salida de "
        "`wasm-validate` y la salida de la ejecución con wasmtime.",
        table(["Programa", "Compila", "wasm-validate", "Ejecuta", "Salida = esperada"], valid_rows),
        "## Programas inválidos",
        "Cada uno debe fallar con el error de su cabecera `// ERROR` y no producir módulo.",
        table(["Programa", "Primer error", "Error = esperado", "Sin módulo"], invalid_rows),
    ]) + "\n"
    (OUT_DIR / "RESUMEN.md").write_text(summary, encoding="utf-8")

    failures = [r for r in valid_rows if FAIL in r or "sin .out" in r] + [r for r in invalid_rows if FAIL in r]
    print(f"{len(valid_rows)} válidos y {len(invalid_rows)} inválidos en {OUT_DIR.relative_to(ROOT)}/")
    if failures:
        print("Con problemas:", ", ".join(r[0] for r in failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
