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
from rustiq.types import BOOL, UNIT, Type


class ControlMixin:
    def visitBlock(self, ctx: RustiQParser.BlockContext):
        self.push_scope()
        for statement in ctx.statement():
            self.visit(statement)
        tail = self.visit(ctx.expression()) if ctx.expression() is not None else UNIT
        if ctx.expression() is not None:
            self.consume(ctx.expression())
        self.pop_scope()
        if tail is not None:
            self.info.expr_type.put(ctx, tail)
        return tail

    def visitExprStmt(self, ctx: RustiQParser.ExprStmtContext):
        actual = self.visit(ctx.expression())
        if actual is not None:
            self.info.expr_type.put(ctx.expression(), actual)  # el codegen descarta el valor
        if hasattr(self, "clear_temporary_borrows"):
            self.clear_temporary_borrows()

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
        self.branch_end(before, branches)

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
        self.mismatch(condition, E_TYPE_MISMATCH, BOOL, self.visit(condition), "La condición")

    def _check_statement_block(self, block: RustiQParser.BlockContext, what: str) -> None:
        actual = self.visit(block)
        if actual is not None and actual != UNIT:
            self.error(
                block.expression(), E_TYPE_MISMATCH,
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
        symbol = self.declare(name, declared, False, "const", ctx.IDENT())
        if symbol is not None:
            self.info.symbol.put(ctx, symbol)
