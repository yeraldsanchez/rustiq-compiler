"""Pipeline completo: parse, semántica, codegen, wat2wasm y wasm-validate.

Dueño: A (Yerald). Es el punto de entrada que usan las pruebas, la CLI y el
servidor. Cada fase solo corre si la anterior terminó sin errores, y si hay
un solo error nunca se devuelve wasm (contrato 6).
"""

import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener
from wasmtime import Engine, Module, WasmtimeError
from wasmtime import wat2wasm as wasmtime_wat2wasm

from rustiq.codegen.emitter import Emitter
from rustiq.errors import (
    BACKEND,
    E_INTERNAL,
    E_INVALID_CHAR,
    E_SYNTAX,
    E_WASM_INVALID,
    E_WAT_INVALID,
    LEXICO,
    SEMANTICO,
    SINTACTICO,
    CompileError,
)
from rustiq.generated.RustiQLexer import RustiQLexer
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.analyzer import Analyzer

WAT2WASM = "wat2wasm"
WASM_VALIDATE = "wasm-validate"
TOOL_TIMEOUT_S = 10

# El parser y los visitors son recursivos: cada paréntesis o bloque anidado suma
# varios marcos. La compilación corre en un hilo con pila grande y un límite de
# recursión alto, así un programa muy anidado no tumba el proceso.
RECURSION_LIMIT = 100_000
THREAD_STACK_BYTES = 512 * 1024 * 1024

# Los errores de backend no apuntan a una línea del programa fuente.
BACKEND_LINE, BACKEND_COLUMN = 1, 1


@dataclass
class CompileResult:
    ok: bool
    errors: list[CompileError] = field(default_factory=list)
    wat: str | None = None
    wasm: bytes | None = None


class BackendError(Exception):
    """Fallo al convertir o validar el módulo. Lleva el CompileError listo."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.error = CompileError(BACKEND, code, message, BACKEND_LINE, BACKEND_COLUMN)


# --- Parse -----------------------------------------------------------------


class _ErrorCollector(ErrorListener):
    """PROVISIONAL hasta que llegue `rustiq/syntax_errors.py` (B, Byron).

    Junta los errores de ANTLR como CompileError en vez de imprimirlos.
    Byron lo reemplaza con códigos precisos y mensajes en español.
    """

    def __init__(self, phase: str, code: str) -> None:
        super().__init__()
        self.phase, self.code = phase, code
        self.errors: list[CompileError] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        text = getattr(offendingSymbol, "text", None)
        length = len(text) if text and text != "<EOF>" else 1
        self.errors.append(
            CompileError(self.phase, self.code, f"Error: {msg}", line, column + 1, length)
        )


def parse_source(source: str):
    """Devuelve (árbol, errores léxicos y sintácticos ordenados por posición)."""
    lexer = RustiQLexer(InputStream(source))
    parser = RustiQParser(CommonTokenStream(lexer))
    lex_errors = _ErrorCollector(LEXICO, E_INVALID_CHAR)
    syntax_errors = _ErrorCollector(SINTACTICO, E_SYNTAX)
    for recognizer, listener in ((lexer, lex_errors), (parser, syntax_errors)):
        recognizer.removeErrorListeners()
        recognizer.addErrorListener(listener)

    tree = parser.program()
    errors = sorted(lex_errors.errors + syntax_errors.errors, key=lambda e: (e.line, e.column))
    return tree, errors


# --- Backend ---------------------------------------------------------------


def _run_tool(args: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=TOOL_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        raise BackendError(E_INTERNAL, f"{args[0]} tardó más de {TOOL_TIMEOUT_S} s")


def wat_to_wasm(wat: str) -> bytes:
    """Convierte WAT a .wasm con wabt, o con wasmtime si wabt no está instalado."""
    if shutil.which(WAT2WASM) is None:
        try:
            return wasmtime_wat2wasm(wat)
        except WasmtimeError as e:
            raise BackendError(E_WAT_INVALID, f"El WAT generado no es válido: {e}")

    with tempfile.TemporaryDirectory() as tmp:
        wat_file, wasm_file = Path(tmp) / "modulo.wat", Path(tmp) / "modulo.wasm"
        wat_file.write_text(wat, encoding="utf-8")
        proc = _run_tool([WAT2WASM, str(wat_file), "-o", str(wasm_file)])
        if proc.returncode != 0:
            raise BackendError(E_WAT_INVALID, f"El WAT generado no es válido: {proc.stderr.strip()}")
        return wasm_file.read_bytes()


def validate_wasm(wasm: bytes) -> None:
    """Valida el módulo con wasm-validate, o con wasmtime si wabt no está instalado."""
    if shutil.which(WASM_VALIDATE) is None:
        try:
            Module.validate(Engine(), wasm)
        except WasmtimeError as e:
            raise BackendError(E_WASM_INVALID, f"El módulo .wasm no es válido: {e}")
        return

    with tempfile.TemporaryDirectory() as tmp:
        wasm_file = Path(tmp) / "modulo.wasm"
        wasm_file.write_bytes(wasm)
        proc = _run_tool([WASM_VALIDATE, str(wasm_file)])
        if proc.returncode != 0:
            raise BackendError(E_WASM_INVALID, f"El módulo .wasm no es válido: {proc.stderr.strip()}")


def assemble(wat: str) -> bytes:
    """WAT -> .wasm validado. Lanza BackendError si algo falla."""
    wasm = wat_to_wasm(wat)
    validate_wasm(wasm)
    return wasm


# --- Pipeline --------------------------------------------------------------


def _internal_error(phase: str, exc: Exception) -> CompileError:
    message = f"Error interno del compilador: {type(exc).__name__}: {exc}"
    return CompileError(phase, E_INTERNAL, message, BACKEND_LINE, BACKEND_COLUMN)


def _failure(errors: list[CompileError]) -> CompileResult:
    return CompileResult(ok=False, errors=errors)


def compile_source(source: str) -> CompileResult:
    """Compila un programa RustiQ. Si hay un solo error, no devuelve wasm.

    Corre en un hilo con pila grande (ver RECURSION_LIMIT).
    """
    outcome: list[CompileResult] = []

    def run() -> None:
        try:
            outcome.append(_compile(source))
        except RecursionError as e:  # anidación más allá incluso del límite alto
            outcome.append(_failure([_internal_error(SINTACTICO, e)]))

    # El límite no se restaura: otro hilo del servidor puede estar compilando.
    if sys.getrecursionlimit() < RECURSION_LIMIT:
        sys.setrecursionlimit(RECURSION_LIMIT)
    previous_stack = threading.stack_size(THREAD_STACK_BYTES)
    try:
        worker = threading.Thread(target=run)
    finally:
        threading.stack_size(previous_stack)
    worker.start()
    worker.join()
    return outcome[0]


def _compile(source: str) -> CompileResult:
    try:
        tree, errors = parse_source(source)
    except Exception as e:  # un bug del parser no debe tumbar el servidor
        return _failure([_internal_error(SINTACTICO, e)])
    if errors:
        return _failure(errors)

    try:
        info, errors = Analyzer().analyze(tree)
    except Exception as e:  # un bug del analizador no debe tumbar el servidor
        return _failure([_internal_error(SEMANTICO, e)])
    if errors:
        return _failure(errors)

    try:
        wat = Emitter(info).generate(tree)
        wasm = assemble(wat)
    except BackendError as e:
        return _failure([e.error])
    except Exception as e:  # un bug del codegen no debe tumbar el servidor
        return _failure([_internal_error(BACKEND, e)])

    return CompileResult(ok=True, wat=wat, wasm=wasm)
