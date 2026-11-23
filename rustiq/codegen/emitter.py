"""Base del generador de WAT.

Hereda un mixin por archivo. Cada mixin implementa solo los `visitX` de sus
reglas. Esta clase aporta lo común: el módulo, las líneas de salida y los
imports del host (ABI en docs/memoria.md).
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from rustiq.codegen.gen_arrays import ArraysGenMixin
from rustiq.codegen.gen_control import ControlGenMixin
from rustiq.codegen.gen_exprs import ExprsGenMixin
from rustiq.codegen.gen_items import ItemsGenMixin, function_name
from rustiq.codegen.gen_match import MatchGenMixin
from rustiq.codegen.gen_refs import RefsGenMixin
from rustiq.codegen.gen_structs import StructsGenMixin
from rustiq.codegen.wasm_types import wasm_type
from rustiq.generated.RustiQVisitor import RustiQVisitor
from rustiq.builtins import HOST_FUNCTIONS
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.semantic.flow import block_tail, expression_diverges
from rustiq.semantic.info import SemanticInfo, Symbol
from rustiq.tree import split_call
from rustiq.types import I32, UNIT, Type

INDENT = "  "
CELL_SIZE = 8  # una celda guarda un escalar (i32 o f64)
PAGE_SIZE = 65536
HEAP_ALIGN = 8
DEFAULT_HEAP_START = 1024

# Allocator y helpers de String que se pegan dentro de cada módulo.
RUNTIME_WAT = (Path(__file__).parent / "runtime.wat").read_text(encoding="utf-8")
# Línea del runtime que fija el inicio del heap. Trae el valor por defecto, así
# runtime.wat también sirve solo (tests/test_runtime.py).
HEAP_GLOBAL = f"(global $heap (mut i32) (i32.const {DEFAULT_HEAP_START}))"
assert RUNTIME_WAT.count(HEAP_GLOBAL) == 1, "runtime.wat debe declarar la global $heap una vez"


def ceil_div(a: int, b: int) -> int:
    return -(-a // b)

@dataclass
class FunctionCtx:
    """Estado de la función que se está emitiendo."""

    name: str
    locals: dict[str, str] = field(default_factory=dict)  # nombre Wasm -> tipo Wasm
    labels: int = 0
    temps: int = 0
    loops: list[tuple[str, str]] = field(default_factory=list)  # (salida, siguiente) de cada ciclo


class Emitter(
    ItemsGenMixin, ControlGenMixin, StructsGenMixin, MatchGenMixin,  # A
    ExprsGenMixin, ArraysGenMixin, RefsGenMixin,  # B
    RustiQVisitor,
):
    def __init__(self, info: SemanticInfo) -> None:
        self.info = info
        self._reset()

    def _reset(self) -> None:
        """Estado de una emisión. `generate` lo reinicia para poder reutilizar el Emitter."""
        self._lines: list[str] = []
        self._depth = 0
        self._fn: FunctionCtx | None = None
        self.global_consts: dict[int, P.ExpressionContext] = {}  # uid -> inicializador
        self._data_segments: list[tuple[int, bytes]] = []  # (dirección, bytes) de cada literal
        self._data_offset = 0  # primera dirección libre de la zona de literales

    # --- Convención de los visitX de expresión ----------------------------
    #
    # Cada `visitX` de expresión deja su valor en la pila de Wasm y devuelve
    # None. Una expresión de tipo () no deja nada. Una sentencia no deja nada.

    def emit(self, line: str = "") -> None:
        self._lines.append(INDENT * self._depth + line)

    @contextmanager
    def indented(self):
        """Las líneas emitidas dentro del `with` van un nivel más adentro."""
        self._depth += 1
        try:
            yield
        finally:
            self._depth -= 1

    # --- Contexto de función ---------------------------------------------

    @property
    def fn(self) -> FunctionCtx:
        assert self._fn is not None, "no hay función en emisión"
        return self._fn

    @staticmethod
    def local_name(symbol: Symbol) -> str:
        """Nombre Wasm del local de un símbolo. El uid evita choques por sombreado."""
        return f"${symbol.name}_{symbol.uid}"

    def load_symbol(self, symbol: Symbol) -> None:
        """Deja el valor de un símbolo en la pila. Lo usan los visitX de identificadores.

        Una constante global se expande en cada uso volviendo a emitir su
        inicializador; el resto vive en un local.
        """
        initializer = self.global_consts.get(symbol.uid)
        if initializer is not None:
            self.visit(initializer)
        elif symbol.address_taken:
            self.emit(f"local.get {self.cell_name(symbol)}")
            self.emit(f"{wasm_type(symbol.type)}.load")
        else:
            self.emit(f"local.get {self.local_name(symbol)}")

    def store_symbol(self, symbol: Symbol, emit_value) -> None:
        """Guarda en el símbolo el valor que deja `emit_value()`, en su local o en su celda."""
        if symbol.address_taken:
            self.emit(f"local.get {self.cell_name(symbol)}")
            emit_value()
            self.emit(f"{wasm_type(symbol.type)}.store")
        else:
            emit_value()
            self.emit(f"local.set {self.local_name(symbol)}")

    @staticmethod
    def cell_name(symbol: Symbol) -> str:
        """Local con la dirección de la celda de un escalar con `&` aplicado."""
        return f"${symbol.name}_{symbol.uid}_cell"

    def alloc_cell(self, symbol: Symbol) -> None:
        """Reserva la celda de un escalar con `&` aplicado y guarda su dirección."""
        cell = self.declare_local(self.cell_name(symbol), I32)
        self.emit(f"i32.const {CELL_SIZE}")
        self.emit("call $alloc")
        self.emit(f"local.set {cell}")

    def declare_local(self, name: str, t: Type) -> str:
        """Declara un local (una sola vez) y devuelve su nombre Wasm."""
        self.fn.locals.setdefault(name, wasm_type(t))
        return name

    def declare_symbol(self, symbol: Symbol) -> str:
        """Declara el local del símbolo. Si vive en una celda, también la reserva."""
        if symbol.address_taken:
            self.alloc_cell(symbol)
        return self.declare_local(self.local_name(symbol), symbol.type)

    def new_temp(self, t: Type) -> str:
        """Local temporal fresco, por ejemplo para guardar un puntero."""
        self.fn.temps += 1
        return self.declare_local(f"$tmp{self.fn.temps}", t)

    def new_pointer_temp(self) -> str:
        """Local temporal para guardar una dirección de memoria."""
        return self.new_temp(I32)

    def new_label(self, prefix: str) -> str:
        """Etiqueta única dentro de la función, para block, loop e if."""
        self.fn.labels += 1
        return f"${prefix}{self.fn.labels}"

    # --- Módulo -------------------------------------------------------------

    def generate(self, tree) -> str:
        """Devuelve el módulo WAT completo.

        Las funciones se emiten primero, aparte: hasta recorrerlas no se conocen los
        literales de String, y de ellos depende dónde empieza el heap.
        """
        self._reset()
        with self.indented():
            self.visit(tree)
        functions, self._lines = self._lines, []
        heap_start = self._heap_start()

        self.emit("(module")
        with self.indented():
            for name, param_type in HOST_FUNCTIONS:
                self.emit(f'(import "env" "{name}" (func ${name} (param {wasm_type(param_type)})))')
            self.emit(f'(memory (export "memory") {ceil_div(heap_start, PAGE_SIZE)})')
            runtime = RUNTIME_WAT.replace(HEAP_GLOBAL, f"(global $heap (mut i32) (i32.const {heap_start}))")
            for line in runtime.splitlines():
                self.emit(line)
            self._lines.extend(functions)
            for offset, data in self._data_segments:
                escaped = "".join(f"\\{b:02x}" for b in data)
                self.emit(f'(data (i32.const {offset}) "{escaped}")')
        self.emit(")")
        return "\n".join(self._lines) + "\n"

    def _heap_start(self) -> int:
        """El heap empieza después de los literales: en 1024 o más allá (alineado) si no caben."""
        return max(DEFAULT_HEAP_START, ceil_div(self._data_offset, HEAP_ALIGN) * HEAP_ALIGN)

    def visitProgram(self, ctx: P.ProgramContext):
        for item in ctx.item():
            decl = item.constDecl()
            symbol = self.info.symbol.get(decl) if decl is not None else None
            if symbol is not None:
                self.global_consts[symbol.uid] = decl.expression()
        for item in ctx.item():
            self.visit(item)

    def visitItem(self, ctx: P.ItemContext):
        # Structs y enums no emiten código por sí mismos; las constantes llegan después.
        if ctx.functionDecl() is not None:
            self.visit(ctx.functionDecl())

    def visitFunctionDecl(self, ctx: P.FunctionDeclContext):
        name = ctx.IDENT().getText()
        sig = self.info.functions[name]
        self._fn = FunctionCtx(name)

        # El cuerpo se emite aparte: sus locales solo se conocen al terminar.
        outer_lines, self._lines = self._lines, []
        outer_depth, self._depth = self._depth, self._depth + 1
        self._box_params(ctx)
        self.visit(ctx.block())
        tail = block_tail(ctx.block())
        if sig.ret != UNIT and (tail is None or expression_diverges(tail)):
            # Sin expresión final, todos los caminos terminan en return o en un loop sin
            # salida (lo garantiza el análisis). `unreachable` cierra el tipo de la función.
            self.emit("unreachable")
        body, self._lines = self._lines, outer_lines
        self._depth = outer_depth

        params = self._param_names(ctx, sig)
        header = f"(func {function_name(name)}"
        if name == "main":
            header += ' (export "main")'
        for pname, (_, ptype) in zip(params, sig.params):
            header += f" (param {pname} {wasm_type(ptype)})"
        if sig.ret != UNIT:
            header += f" (result {wasm_type(sig.ret)})"
        self.emit(header)
        with self.indented():
            for lname, ltype in self.fn.locals.items():
                self.emit(f"(local {lname} {ltype})")
        self._lines.extend(body)
        self.emit(")")
        self._fn = None

    def _box_params(self, ctx: P.FunctionDeclContext) -> None:
        """Copia a una celda cada parámetro escalar con `&` aplicado, al entrar."""
        if ctx.parameterList() is None:
            return
        for p in ctx.parameterList().parameter():
            symbol = self.info.symbol.get(p)
            if symbol is not None and symbol.address_taken:
                self.alloc_cell(symbol)
                self.emit(f"local.get {self.cell_name(symbol)}")
                self.emit(f"local.get {self.local_name(symbol)}")
                self.emit(f"{wasm_type(symbol.type)}.store")

    def _param_names(self, ctx: P.FunctionDeclContext, sig) -> list[str]:
        """Nombre Wasm de cada parámetro: por uid si hay símbolo, si no por posición."""
        if ctx.parameterList() is None:
            return []
        names = []
        for i, p in enumerate(ctx.parameterList().parameter()):
            symbol = self.info.symbol.get(p)
            names.append(self.local_name(symbol) if symbol else f"$p{i}")
        return names

    # --- Espina compartida de `postfix` (ver analyzer.py) -----------------------
    #
    # Cada sufijo encuentra el valor del operando en la pila y recibe su tipo en
    # `info.expr_type[sufijo]`.

    def visitPostfix(self, ctx: P.PostfixContext):
        self.emit_postfix(ctx.primary(), ctx.children[1:])

    def emit_postfix(self, primary, suffixes: list) -> None:
        """Emite `primary` seguido de los sufijos dados (todos o solo los primeros)."""
        call, suffixes = split_call(primary, suffixes)
        if call is not None:
            self.gen_call(primary, call)
        else:
            self.visit(primary)
        for suffix in suffixes:
            self.visit(suffix)

    def visitConstDecl(self, ctx: P.ConstDeclContext):
        return None  # las constantes globales se expanden en cada uso
