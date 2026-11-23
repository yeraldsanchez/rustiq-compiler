"""Divergencia: ¿un bloque termina siempre en return, break o continue?

Funciones puras sobre el árbol. Sirven para decidir si una función con tipo de
retorno puede no tener expresión final (`return` en todas las ramas, un `match`
con `return` en todos los brazos, o un `loop` sin `break`).
"""

from antlr4 import ParserRuleContext

from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.tree import unwrap


def block_tail(block: P.BlockContext):
    """La expresión final del bloque, o None.

    ANTLR lee `{ { 3 } }` con el bloque interno como sentencia (BlockS), porque
    `statement` va antes que la expresión final en la regla `block`. Si la última
    sentencia es un bloque que produce valor y no hay otra expresión final, ese
    bloque es la expresión final (devuelve su BlockContext).
    """
    if block.expression() is not None:
        return block.expression()
    statements = block.statement()
    if statements and isinstance(statements[-1], P.BlockSContext):
        inner = statements[-1].block()
        if block_tail(inner) is not None:
            return inner
    return None


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
    if isinstance(stmt, P.ExprStmtContext):
        return expression_diverges(stmt.expression())
    return False


def expression_diverges(expression) -> bool:
    """Un bloque que diverge, o un `match` cuyos brazos divergen todos."""
    primary = bare_primary(expression)
    if isinstance(primary, P.BlockPContext):
        return block_diverges(primary.block())
    if isinstance(expression, P.BlockContext):  # bloque promovido por block_tail
        return block_diverges(expression)
    if isinstance(primary, P.MatchPContext):
        return all(expression_diverges(arm.expression()) for arm in primary.matchExpr().matchArm())
    return False


def bare_primary(expression):
    """El `primary` si la expresión es solo eso (sin operadores ni sufijos), si no None."""
    node = expression
    while node is not None:
        if isinstance(node, P.PostfixContext):
            return node.primary() if node.getChildCount() == 1 else None
        node = unwrap(node)
    return None


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
