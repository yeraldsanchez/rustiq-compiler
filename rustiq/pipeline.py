"""Pipeline completo: parse, semántica, codegen, wat2wasm y wasm-validate.

Es el punto de entrada que usan las pruebas, la CLI y el
servidor. Cada fase solo corre si la anterior terminó sin errores, y si hay
un solo error nunca se devuelve wasm.
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
    E_INVALID_ESCAPE,
    E_UNTERMINATED_COMMENT,
    E_UNTERMINATED_STRING,
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
from rustiq.symbols import SymbolHint, collect_symbols

WAT2WASM = "wat2wasm"
WASM_VALIDATE = "wasm-validate"
TOOL_TIMEOUT_S = 10

# El parser y los visitors son recursivos: cada paréntesis o bloque anidado suma
# varios marcos. La compilación corre en un hilo con pila grande y un límite de
# recursión alto, así un programa muy anidado no tumba el proceso.
RECURSION_LIMIT = 100_000

# Tamaño deseado de la pila del hilo de compilación. En Linux/CI 512 MB es
# suficiente y barato (solo reserva virtual). Windows rechaza valores muy
# grandes con ``ValueError`` al llamar ``threading.stack_size``; en ese caso
# bajamos escalonadamente hasta encontrar uno soportado por la plataforma.
THREAD_STACK_BYTES = 512 * 1024 * 1024

# Probamos de mayor a menor hasta que la plataforma acepte uno. El primero
# (512 MB) es el que usa CI/Linux; en Windows típicamente cae a 32–64 MB, que
# alcanzan sobrado para ``test_anidacion.py``.
STACK_SIZE_FALLBACKS: tuple[int, ...] = (
    THREAD_STACK_BYTES,     # 512 MB  — Linux / CI
    256 * 1024 * 1024,
    128 * 1024 * 1024,
    64 * 1024 * 1024,
    32 * 1024 * 1024,
    16 * 1024 * 1024,
    8 * 1024 * 1024,        # último recurso: ~pila por defecto en Linux
)

# Los errores de backend no apuntan a una línea del programa fuente.
BACKEND_LINE, BACKEND_COLUMN = 1, 1


@dataclass
class CompileResult:
    ok: bool
    errors: list[CompileError] = field(default_factory=list)
    wat: str | None = None
    wasm: bytes | None = None
    # Para el editor: qué es cada identificador. Llega aunque haya errores
    # semánticos; con errores de sintaxis queda vacío.
    symbols: list[SymbolHint] = field(default_factory=list)


class BackendError(Exception):
    """Fallo al convertir o validar el módulo. Lleva el CompileError listo."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.error = CompileError(BACKEND, code, message, BACKEND_LINE, BACKEND_COLUMN)


# --- Parse -----------------------------------------------------------------


class _SyntaxErrorCollector(ErrorListener):
    """Errores sintácticos de ANTLR como CompileError en vez de imprimirlos.

    Los léxicos van aparte: `_LexErrorCollector` y los tokens de error del lexer.
    """

    def __init__(self) -> None:
        super().__init__()
        self.errors: list[CompileError] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        text = getattr(offendingSymbol, "text", None)
        length = len(text) if text and text != "<EOF>" else 1
        self.errors.append(
            CompileError(SINTACTICO, E_SYNTAX, f"Error: {msg}", line, column + 1, length)
        )


class _LexErrorCollector(ErrorListener):
    """Caracteres que no forman ningún token (`#`, `ñ`, `@`...)."""

    def __init__(self) -> None:
        super().__init__()
        self.errors: list[CompileError] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        lexer = recognizer
        char = lexer._input.getText(lexer._tokenStartCharIndex, lexer._tokenStartCharIndex)
        self.errors.append(
            CompileError(LEXICO, E_INVALID_CHAR, f"Carácter no válido: {char!r}", line, column + 1, 1)
        )


VALID_ESCAPES = set("ntr\\\"'")
ESCAPES_HELP = "se aceptan \\n, \\t, \\r, \\\\, \\\" y \\'"


def _bad_escape(token) -> CompileError | None:
    """El primer escape no válido dentro de un literal, o None."""
    text = token.text
    i = 1
    while i < len(text) - 1:
        if text[i] == "\\":
            if text[i + 1] not in VALID_ESCAPES:
                return CompileError(
                    LEXICO, E_INVALID_ESCAPE,
                    f"Secuencia de escape no válida '\\{text[i + 1]}'; {ESCAPES_HELP}",
                    token.line, token.column + i + 1, 2,
                )
            i += 2
        else:
            i += 1
    return None


def _error_token(token) -> CompileError:
    """Convierte un token de error del lexer (canal oculto) en un error léxico."""
    T = RustiQLexer
    line, column, length = token.line, token.column + 1, max(len(token.text), 1)
    if token.type == T.UNTERMINATED_COMMENT:
        return CompileError(LEXICO, E_UNTERMINATED_COMMENT, "Comentario de bloque sin cerrar: falta '*/'", line, column, 2)
    if token.type == T.UNTERMINATED_STRING:
        return CompileError(
            LEXICO, E_UNTERMINATED_STRING,
            "String sin cerrar: falta la comilla '\"' antes del fin de la línea", line, column, length,
        )
    if token.type == T.UNTERMINATED_CHAR:
        return CompileError(
            LEXICO, E_INVALID_CHAR, "Literal char sin cerrar: falta la comilla \"'\"", line, column, length,
        )
    escape = _bad_escape(token)
    if escape is not None:
        return escape
    return CompileError(  # BAD_CHAR sin escapes malos: vacío o con varios caracteres
        LEXICO, E_INVALID_CHAR, "Un literal char lleva exactamente un carácter", line, column, length,
    )


ERROR_TOKENS = {
    RustiQLexer.BAD_STRING,
    RustiQLexer.UNTERMINATED_STRING,
    RustiQLexer.BAD_CHAR,
    RustiQLexer.UNTERMINATED_CHAR,
    RustiQLexer.UNTERMINATED_COMMENT,
}


def parse_source(source: str):
    """Devuelve (árbol, errores léxicos y sintácticos ordenados por posición)."""
    lexer = RustiQLexer(InputStream(source))
    tokens = CommonTokenStream(lexer)
    parser = RustiQParser(tokens)
    lex_errors = _LexErrorCollector()
    syntax_errors = _SyntaxErrorCollector()
    for recognizer, listener in ((lexer, lex_errors), (parser, syntax_errors)):
        recognizer.removeErrorListeners()
        recognizer.addErrorListener(listener)

    tokens.fill()
    token_errors = [_error_token(t) for t in tokens.tokens if t.type in ERROR_TOKENS]
    tree = parser.program()
    errors = lex_errors.errors + token_errors + syntax_errors.errors
    return tree, sorted(errors, key=lambda e: (e.line, e.column))


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


def _failure(errors: list[CompileError], symbols: list[SymbolHint] | None = None) -> CompileResult:
    return CompileResult(ok=False, errors=errors, symbols=symbols or [])


def _safe_symbols(tree, info) -> list[SymbolHint]:
    """Los símbolos son una ayuda del editor: si fallan, no afectan la compilación."""
    try:
        return collect_symbols(tree, info)
    except Exception:
        return []


def _apply_thread_stack_size() -> int:
    """Fija el tamaño de pila más grande que acepte la plataforma.

    Devuelve el valor previo para poder restaurarlo. En Windows
    ``threading.stack_size(512 MB)`` lanza ``ValueError``; caemos a tamaños
    menores (``STACK_SIZE_FALLBACKS``) hasta encontrar uno válido. En
    Linux/CI el primero (512 MB) ya funciona.
    """
    previous = threading.stack_size()
    for size in STACK_SIZE_FALLBACKS:
        try:
            threading.stack_size(size)
            return previous
        except (ValueError, RuntimeError):
            continue
    # Ningún tamaño fue aceptado por la plataforma: dejamos el anterior.
    return previous


def compile_source(source: str) -> CompileResult:
    """Compila un programa RustiQ. Si hay un solo error, no devuelve wasm.

    Corre en un hilo con pila grande (ver RECURSION_LIMIT). El tamaño de pila
    se selecciona con ``_apply_thread_stack_size`` y debe estar vigente al
    llamar ``start()``: en CPython el tamaño efectivo del hilo se fija en ese
    momento, no al construir el ``Thread``.
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

    previous_stack = _apply_thread_stack_size()
    try:
        worker = threading.Thread(target=run)
        # start() dentro del try: así el hilo arranca con la pila grande.
        worker.start()
    finally:
        threading.stack_size(previous_stack)
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
    symbols = _safe_symbols(tree, info)
    if errors:
        return _failure(errors, symbols)

    try:
        wat = Emitter(info).generate(tree)
        wasm = assemble(wat)
    except BackendError as e:
        return _failure([e.error], symbols)
    except Exception as e:  # un bug del codegen no debe tumbar el servidor
        return _failure([_internal_error(BACKEND, e)], symbols)

    return CompileResult(ok=True, wat=wat, wasm=wasm, symbols=symbols)