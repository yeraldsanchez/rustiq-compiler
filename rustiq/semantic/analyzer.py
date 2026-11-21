"""Contrato 7: visitor principal del anÃ¡lisis semÃ¡ntico.

Hereda un mixin por archivo. Cada mixin implementa solo los `visitX` de sus
reglas. Esta clase aporta lo comÃºn: `info`, `errors` y `error()`.
"""

from antlr4 import ParserRuleContext
from antlr4.tree.Tree import TerminalNode

from rustiq.errors import E_NOT_CALLABLE, SEMANTICO, CompileError
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.generated.RustiQVisitor import RustiQVisitor
from rustiq.semantic.borrows import BorrowsMixin
from rustiq.semantic.check_arrays import ArraysMixin
from rustiq.semantic.check_control import ControlMixin
from rustiq.semantic.check_exprs import ExprsMixin
from rustiq.semantic.check_items import ItemsMixin
from rustiq.semantic.check_match import MatchMixin
from rustiq.semantic.check_refs import RefsMixin
from rustiq.semantic.check_structs import StructsMixin
from rustiq.semantic.info import SemanticInfo
from rustiq.semantic.moves import MovesMixin
from rustiq.semantic.scope_defaults import ScopeDefaults
from rustiq.semantic.scopes import ScopesMixin
from rustiq.types import Type


class Analyzer(
    ItemsMixin, StructsMixin, BorrowsMixin, ControlMixin, MatchMixin, MovesMixin,  # A/B
    ScopesMixin, ExprsMixin, ArraysMixin, RefsMixin,  # B
    ScopeDefaults,  # respaldo del contrato de Ã¡mbitos; ScopesMixin lo reemplaza
    RustiQVisitor,
):
    def __init__(self) -> None:
        self.info = SemanticInfo()
        self.errors: list[CompileError] = []
        self.type_names: dict[str, Type] = {}  # structs y enums declarados
        self.fn_ret: Type | None = None  # tipo de retorno de la funciÃ³n en anÃ¡lisis
        self.loop_depth = 0  # ciclos abiertos, para break y continue
        self.move_states: dict[int, str] = {}  # uid -> estado (moves.py)
        self.move_loop_depth: dict[int, int] = {}  # uid -> ciclos abiertos al declararlo
        self.moved_in_branches: list[set[int]] = []  # uids movidos en cada if/match abierto

    def analyze(self, tree) -> tuple[SemanticInfo, list[CompileError]]:
        self.visit(tree)
        return self.info, self.errors

    def error(self, node, code: str, message: str) -> None:
        """Registra un error semÃ¡ntico en la posiciÃ³n del nodo."""
        self.errors.append(
            CompileError(SEMANTICO, code, message, *self._position(node))
        )

    @staticmethod
    def _position(node) -> tuple[int, int, int]:
        """(lÃ­nea desde 1, columna desde 1, largo) del nodo."""
        if isinstance(node, TerminalNode):
            token = node.symbol
            return token.line, token.column + 1, len(token.text)
        assert isinstance(node, ParserRuleContext)
        start, stop = node.start, node.stop
        if stop is not None and stop.line == start.line:
            length = stop.stop - start.start + 1
        else:
            length = len(start.text)
        return start.line, start.column + 1, length

    # --- Espina compartida de `postfix` ------------------------------------
    #
    # ConvenciÃ³n: todo `visitX` de expresiÃ³n devuelve su `Type` (None si ya hubo
    # un error que lo impide). Cada sufijo recibe el tipo del operando en
    # `info.expr_type[sufijo]` y devuelve el tipo del resultado.
    #   - visitCallSuffix: A (solo llamadas por nombre se resuelven aquÃ­)
    #   - visitFieldSuffix: A
    #   - visitIndexSuffix: B

    def visitPostfix(self, ctx: RustiQParser.PostfixContext):
        primary = ctx.primary()
        suffixes = ctx.children[1:]
        if suffixes and isinstance(suffixes[0], RustiQParser.CallSuffixContext) and isinstance(
            primary, RustiQParser.IdentPContext
        ):
            current = self.check_call(primary, suffixes[0])
            suffixes = suffixes[1:]
        else:
            current = self.visit(primary)
        for suffix in suffixes:
            if current is not None:
                self.info.expr_type.put(suffix, current)
            current = self.visit(suffix) if current is not None else None
        if current is not None:
            self.info.expr_type.put(ctx, current)
        return current

    def visitCallSuffix(self, ctx: RustiQParser.CallSuffixContext):
        self.error(ctx, E_NOT_CALLABLE, "Solo se pueden llamar funciones por su nombre")
        return None

    def mismatch(self, node, code: str, expected: Type, actual: Type | None, what: str) -> bool:
        """Registra un error si los tipos difieren. Si `actual` es None (error previo) calla."""
        if actual is None or actual == expected:
            return False
        self.error(node, code, f"{what}: se esperaba {expected} y se encontrÃ³ {actual}")
        return True
