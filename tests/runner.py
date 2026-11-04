"""Runner de la suite de programas .rq.

Formato (ver tests/README.md):
- tests/valid/<nombre>.rq con tests/valid/<nombre>.out, la salida exacta esperada.
- tests/invalid/<nombre>.rq con la primera línea `// ERROR <fase> <codigo> <linea>:<columna>`.

Se compara fase, código, línea y columna del primer error. El mensaje puede
cambiar sin romper pruebas.
"""

import re
from dataclasses import dataclass
from pathlib import Path

TESTS_DIR = Path(__file__).parent
VALID_DIR = TESTS_DIR / "valid"
INVALID_DIR = TESTS_DIR / "invalid"

_ERROR_HEADER = re.compile(r"^//\s*ERROR\s+(\w+)\s+(\w+)\s+(\d+):(\d+)\s*$")


@dataclass(frozen=True)
class ExpectedError:
    phase: str
    code: str
    line: int
    column: int


def parse_expected_error(source: str) -> ExpectedError | None:
    """Lee la cabecera `// ERROR ...` de la primera línea, o None si no hay."""
    lines = source.splitlines()
    match = _ERROR_HEADER.match(lines[0]) if lines else None
    if match is None:
        return None
    phase, code, line, column = match.groups()
    return ExpectedError(phase, code, int(line), int(column))


def valid_cases() -> list[Path]:
    return sorted(VALID_DIR.glob("*.rq"))


def invalid_cases() -> list[Path]:
    return sorted(INVALID_DIR.glob("*.rq"))


def check_valid(rq: Path, compile_source, run_wasm) -> None:
    """Compila el programa, lo ejecuta y compara con el `.out`."""
    result = compile_source(rq.read_text(encoding="utf-8"))
    assert result.ok, f"{rq.name} debía compilar y dio: {result.errors}"
    esperado = rq.with_suffix(".out").read_text(encoding="utf-8")
    assert run_wasm(result.wasm) == esperado


def check_invalid(rq: Path, compile_source) -> None:
    """Compila el programa y comprueba que falle con el error de la cabecera."""
    source = rq.read_text(encoding="utf-8")
    esperado = parse_expected_error(source)
    assert esperado is not None, f"{rq.name} no tiene la cabecera // ERROR"

    result = compile_source(source)
    assert not result.ok, f"{rq.name} debía fallar y compiló"
    assert result.wasm is None, "con un error nunca se devuelve wasm"
    primero = result.errors[0]
    obtenido = ExpectedError(primero.phase, primero.code, primero.line, primero.column)
    assert obtenido == esperado
