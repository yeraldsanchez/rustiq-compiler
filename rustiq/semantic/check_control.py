"""Control de flujo y bloques: if, while, loop, break, continue, return.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas; si necesita algo de
otro mixin, llama su método público y nunca copia la lógica.

`if` es solo sentencia (P4): sus ramas, y el cuerpo de `while` y `loop`, no
pueden producir valor. Un bloque usado como expresión sí.
"""

from rustiq.errors import (
    E_BAD_RETURN,
    E_BREAK_OUTSIDE_LOOP,
    E_TYPE_MISMATCH,
)
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.flow import block_tail
from rustiq.semantic.info import SymbolKind
from rustiq.types import BOOL, UNIT, Type


class ControlMixin:
    def visitBlock(self, ctx: RustiQParser.BlockContext):
        self.push_scope()
        tail_node = block_tail(ctx)
        statements = ctx.statement()
        if tail_node is not None and tail_node is not ctx.expression():
            statements = statements[:-1]  # `{ { 3 } }`: el bloque interno es el valor
        for statement in statements:
            mark = self.borrow_mark()
            self.visit(statement)
            self.release_temporary_borrows(mark)
        tail = self.visit(tail_node) if tail_node is not None else UNIT
        if tail_node is not None:
            self.consume(tail_node)
        self.pop_scope()
        if tail is not None:
            self.info.expr_type.put(ctx, tail)
        return tail

    def visitExprStmt(self, ctx: RustiQParser.ExprStmtContext):
        actual = self.visit(ctx.expression())
        if actual is not None:
            self.info.expr_type.put(ctx.expression(), actual)  # el codegen descarta el valor

    def visitBlockS(self, ctx: RustiQParser.BlockSContext):
        self._check_statement_block(ctx.block(), "Un bloque usado como sentencia")

    # --- if / while / loop -----------------------------------------------

    def visitIfStmt(self, ctx: RustiQParser.IfStmtContext):
        self._check_condition(ctx.condition())
        before, branches = self.branch_start(), []
        for block in ctx.block():
            self.branch_restore(before)
            self._check_statement_block(block, "Una rama de if")
            branches.append(self.move_states)
        if ctx.ifStmt() is not None:
            self.branch_restore(before)
            self.visit(ctx.ifStmt())
            branches.append(self.move_states)
        has_else = len(ctx.block()) == 2 or ctx.ifStmt() is not None
        self.branch_end(before, branches, exhaustive=has_else)

    def visitWhileStmt(self, ctx: RustiQParser.WhileStmtContext):
        self._check_condition(ctx.condition())
        self._check_loop_body(ctx.block(), "El cuerpo de while")

    def visitLoopStmt(self, ctx: RustiQParser.LoopStmtContext):
        self._check_loop_body(ctx.block(), "El cuerpo de loop")

    def _check_loop_body(self, block, what: str) -> None:
        self.loop_depth += 1
        self._check_statement_block(block, what)
        self.loop_depth -= 1

    def _check_condition(self, condition: RustiQParser.ConditionContext) -> None:
        mark = self.borrow_mark()  # los préstamos de la condición no llegan al cuerpo
        self.mismatch(condition, E_TYPE_MISMATCH, BOOL, self.visit(condition), "La condición")
        self.release_temporary_borrows(mark)

    def _check_statement_block(self, block: RustiQParser.BlockContext, what: str) -> None:
        actual = self.visit(block)
        if actual is not None and actual != UNIT:
            self.error(
                block_tail(block), E_TYPE_MISMATCH,
                f"{what} no puede producir un valor ({actual}); agrega ';' o usa return",
            )

    # --- break / continue / return -------------------------------------------

    def visitBreakStmt(self, ctx: RustiQParser.BreakStmtContext):
        self._check_inside_loop(ctx, "break")

    def visitContinueStmt(self, ctx: RustiQParser.ContinueStmtContext):
        self._check_inside_loop(ctx, "continue")

    def _check_inside_loop(self, ctx, keyword: str) -> None:
        if self.loop_depth == 0:
            self.error(ctx, E_BREAK_OUTSIDE_LOOP, f"'{keyword}' solo puede usarse dentro de while o loop")

    def visitReturnStmt(self, ctx: RustiQParser.ReturnStmtContext):
        expected: Type = self.fn_ret
        if ctx.expression() is None:
            if expected != UNIT:
                self.error(ctx, E_BAD_RETURN, f"Se debe devolver un valor de tipo {expected}")
            return
        actual = self.visit(ctx.expression())
        self.consume(ctx.expression())
        self.check_returned_ref(ctx.expression())
        if expected == UNIT:
            self.error(ctx.expression(), E_BAD_RETURN, "La función no devuelve ningún valor")
        else:
            self.mismatch(ctx.expression(), E_BAD_RETURN, expected, actual, "El valor de return")

    # --- const local --------------------------------------------------------------

    def visitConstLocalDecl(self, ctx: RustiQParser.ConstLocalDeclContext):
        declared = self.resolve_type(ctx.type_())
        name = ctx.IDENT().getText()
        self.mismatch(
            ctx.expression(), E_TYPE_MISMATCH, declared, self.visit(ctx.expression()),
            f"La constante '{name}'",
        )
        symbol = self.declare(name, declared, False, SymbolKind.CONST, ctx.IDENT())
        if symbol is not None:
            self.info.symbol.put(ctx, symbol)
