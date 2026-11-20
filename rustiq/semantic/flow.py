"""Divergencia: ¿un bloque termina siempre en return, break o continue?

Funciones puras sobre el árbol. Sirven para decidir si una función con tipo de
retorno puede no tener expresión final (`return` en todas las ramas, o un
`loop` sin `break`).
"""

from antlr4 import ParserRuleContext

from rustiq.generated.RustiQParser import RustiQParser as P


def block_diverges(block: P.BlockContext) -> bool:
    """Un bloque diverge si alguna de sus sentencias diverge: el resto no se alcanza."""
    return any(_statement_diverges(s) for s in block.statement())


def _statement_diverges(stmt: P.StatementContext) -> bool:
    if isinstance(stmt, (P.ReturnSContext, P.BreakSContext, P.ContinueSContext)):
        return True
    if isinstance(stmt, P.LoopSContext):
        return not has_break(stmt.loopStmt().block())
    if isinstance(stmt, P.IfSContext):
        return _if_diverges(stmt.ifStmt())
    if isinstance(stmt, P.BlockSContext):
        return block_diverges(stmt.block())
    return False


def _if_diverges(stmt: P.IfStmtContext) -> bool:
    """Solo diverge si tiene else y todas las ramas divergen."""
    blocks = stmt.block()
    if not block_diverges(blocks[0]):
        return False
    if len(blocks) == 2:
        return block_diverges(blocks[1])
    if stmt.ifStmt() is not None:
        return _if_diverges(stmt.ifStmt())
    return False


def has_break(node: ParserRuleContext) -> bool:
    """True si hay un `break` que pertenece al ciclo de `node` (no a uno anidado)."""
    for child in node.children or []:
        if isinstance(child, P.BreakStmtContext):
            return True
        if isinstance(child, (P.WhileStmtContext, P.LoopStmtContext)):
            continue
        if isinstance(child, ParserRuleContext) and has_break(child):
            return True
    return False
