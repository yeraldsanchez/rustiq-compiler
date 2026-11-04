"""Contrato 7: visitor principal del análisis semántico.

Hereda un mixin por archivo. Cada mixin implementa solo los `visitX` de sus
reglas. Esta clase aporta lo común: `info`, `errors` y `error()`.
"""

from antlr4 import ParserRuleContext
from antlr4.tree.Tree import TerminalNode

from rustiq.errors import SEMANTICO, CompileError
from rustiq.generated.RustiQVisitor import RustiQVisitor
from rustiq.semantic.borrows import BorrowsMixin
from rustiq.semantic.check_arrays import ArraysMixin
from rustiq.semantic.check_control import ControlMixin
from rustiq.semantic.check_exprs import ExprsMixin
from rustiq.semantic.check_items import ItemsMixin
from rustiq.semantic.check_match import MatchMixin
from rustiq.semantic.check_refs import RefsMixin
from rustiq.semantic.info import SemanticInfo
from rustiq.semantic.moves import MovesMixin
from rustiq.semantic.scopes import ScopesMixin


class Analyzer(
    ItemsMixin, ControlMixin, MatchMixin, MovesMixin,  # A
    ScopesMixin, ExprsMixin, ArraysMixin, RefsMixin,  # B
    BorrowsMixin,  # B
    RustiQVisitor,
):
    def __init__(self) -> None:
        self.info = SemanticInfo()
        self.errors: list[CompileError] = []

    def analyze(self, tree) -> tuple[SemanticInfo, list[CompileError]]:
        self.visit(tree)
        return self.info, self.errors

    def error(self, node, code: str, message: str) -> None:
        """Registra un error semántico en la posición del nodo."""
        self.errors.append(
            CompileError(SEMANTICO, code, message, *self._position(node))
        )

    @staticmethod
    def _position(node) -> tuple[int, int, int]:
        """(línea desde 1, columna desde 1, largo) del nodo."""
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
