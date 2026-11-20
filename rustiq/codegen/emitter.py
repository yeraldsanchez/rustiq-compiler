"""Base del generador de WAT.

Hereda un mixin por archivo. Cada mixin implementa solo los `visitX` de sus
reglas. Esta clase aporta lo común: el módulo, las líneas de salida y los
imports del host (ABI en docs/memoria.md).
"""

from dataclasses import dataclass, field
from pathlib import Path

from rustiq.codegen.gen_arrays import ArraysGenMixin
from rustiq.codegen.gen_control import ControlGenMixin
from rustiq.codegen.gen_exprs import ExprsGenMixin
from rustiq.codegen.gen_items import ItemsGenMixin
from rustiq.codegen.gen_match import MatchGenMixin
from rustiq.codegen.gen_refs import RefsGenMixin
from rustiq.codegen.gen_structs import StructsGenMixin
from rustiq.codegen.wasm_types import wasm_type
from rustiq.generated.RustiQVisitor import RustiQVisitor
from rustiq.builtins import HOST_FUNCTIONS
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.info import SemanticInfo, Symbol
from rustiq.types import UNIT, Type

INDENT = "  "

# Allocator y helpers de String que se pegan dentro de cada módulo.
RUNTIME_WAT = (Path(__file__).parent / "runtime.wat").read_text(encoding="utf-8")

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
        self._lines: list[str] = []
        self._depth = 0
        self._fn: FunctionCtx | None = None
        self.global_consts: dict[int, RustiQParser.ExpressionContext] = {}

    # --- Convención de los visitX de expresión ----------------------------
    #
    # Cada `visitX` de expresión deja su valor en la pila de Wasm y devuelve
    # None. Una expresión de tipo () no deja nada. Una sentencia no deja nada.

    def emit(self, line: str = "") -> None:
        self._lines.append(INDENT * self._depth + line)

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
        else:
            self.emit(f"local.get {self.local_name(symbol)}")

    def declare_local(self, name: str, t: Type) -> str:
        """Declara un local (una sola vez) y devuelve su nombre Wasm."""
        self.fn.locals.setdefault(name, wasm_type(t))
        return name

    def declare_symbol(self, symbol: Symbol) -> str:
        return self.declare_local(self.local_name(symbol), symbol.type)

    def new_temp(self, t: Type) -> str:
        """Local temporal fresco, por ejemplo para guardar un puntero."""
        self.fn.temps += 1
        return self.declare_local(f"$tmp{self.fn.temps}", t)

    def new_label(self, prefix: str) -> str:
        """Etiqueta única dentro de la función, para block, loop e if."""
        self.fn.labels += 1
        return f"${prefix}{self.fn.labels}"

    # --- Módulo -------------------------------------------------------------

    def generate(self, tree) -> str:
        """Devuelve el módulo WAT completo."""
        self._lines = []
        self._depth = 0
        self._fn = None
        self.global_consts = {}
        self.emit("(module")
        self._depth += 1
        for name, param_type in HOST_FUNCTIONS:
            self.emit(f'(import "env" "{name}" (func ${name} (param {wasm_type(param_type)})))')
        self.emit('(memory (export "memory") 1)')
        for line in RUNTIME_WAT.splitlines():
            self.emit(line)
        self.visit(tree)
        self._depth -= 1
        self.emit(")")
        return "\n".join(self._lines) + "\n"

    def visitProgram(self, ctx: RustiQParser.ProgramContext):
        for item in ctx.item():
            decl = item.constDecl()
            symbol = self.info.symbol.get(decl) if decl is not None else None
            if symbol is not None:
                self.global_consts[symbol.uid] = decl.expression()
        for item in ctx.item():
            self.visit(item)

    def visitItem(self, ctx: RustiQParser.ItemContext):
        # Structs y enums no emiten código por sí mismos; las constantes llegan después.
        if ctx.functionDecl() is not None:
            self.visit(ctx.functionDecl())

    def visitFunctionDecl(self, ctx: RustiQParser.FunctionDeclContext):
        name = ctx.IDENT().getText()
        sig = self.info.functions[name]
        self._fn = FunctionCtx(name)

        # El cuerpo se emite aparte: sus locales solo se conocen al terminar.
        outer_lines, self._lines = self._lines, []
        outer_depth, self._depth = self._depth, self._depth + 1
        self.visit(ctx.block())
        if sig.ret != UNIT and ctx.block().expression() is None:
            # Sin expresión final, todos los caminos terminan en return o en un loop sin
            # salida (lo garantiza el análisis). `unreachable` cierra el tipo de la función.
            self.emit("unreachable")
        body, self._lines = self._lines, outer_lines
        self._depth = outer_depth

        params = self._param_names(ctx, sig)
        header = f"(func ${name}"
        if name == "main":
            header += ' (export "main")'
        for pname, (_, ptype) in zip(params, sig.params):
            header += f" (param {pname} {wasm_type(ptype)})"
        if sig.ret != UNIT:
            header += f" (result {wasm_type(sig.ret)})"
        self.emit(header)
        self._depth += 1
        for lname, ltype in self.fn.locals.items():
            self.emit(f"(local {lname} {ltype})")
        self._lines.extend(body)
        self._depth -= 1
        self.emit(")")
        self._fn = None

    def _param_names(self, ctx: RustiQParser.FunctionDeclContext, sig) -> list[str]:
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
    # `info.expr_type[sufijo]`. visitCallSuffix y visitFieldSuffix son de A,
    # visitIndexSuffix de B.

    def visitPostfix(self, ctx: RustiQParser.PostfixContext):
        primary = ctx.primary()
        suffixes = ctx.children[1:]
        if suffixes and isinstance(suffixes[0], RustiQParser.CallSuffixContext) and isinstance(
            primary, RustiQParser.IdentPContext
        ):
            self.gen_call(primary, suffixes[0])
            suffixes = suffixes[1:]
        else:
            self.visit(primary)
        for suffix in suffixes:
            self.visit(suffix)

    def visitConstDecl(self, ctx: RustiQParser.ConstDeclContext):
        return None  # las constantes globales se expanden en cada uso
