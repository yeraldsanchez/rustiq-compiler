"""Generación de código de control de flujo y bloques.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos.

Un bloque no abre un `block` de Wasm: sus sentencias se emiten en secuencia y la
expresión final deja su valor en la pila. Los ciclos usan `block` + `loop` con
etiquetas con nombre, así `break` y `continue` saltan al ciclo correcto sin
contar profundidades.
"""

from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.types import UNIT


class ControlGenMixin:
    def visitBlock(self, ctx: P.BlockContext):
        for statement in ctx.statement():
            self.visit(statement)
        if ctx.expression() is not None:
            self.visit(ctx.expression())

    def visitExprStmt(self, ctx: P.ExprStmtContext):
        self.visit(ctx.expression())
        produced = self.info.expr_type.get(ctx.expression())
        if produced is not None and produced != UNIT:
            self.emit("drop")  # el valor de una sentencia no se usa

    # --- if / while / loop -----------------------------------------------

    def visitIfStmt(self, ctx: P.IfStmtContext):
        self.visit(ctx.condition())
        self.emit("if")
        with self.indented():
            self.visit(ctx.block(0))
        has_else_block = len(ctx.block()) == 2
        if has_else_block or ctx.ifStmt() is not None:
            self.emit("else")
            with self.indented():
                self.visit(ctx.block(1) if has_else_block else ctx.ifStmt())
        self.emit("end")

    def visitWhileStmt(self, ctx: P.WhileStmtContext):
        self._gen_loop(ctx.block(), ctx.condition())

    def visitLoopStmt(self, ctx: P.LoopStmtContext):
        self._gen_loop(ctx.block(), None)

    def _gen_loop(self, body, condition) -> None:
        exit_label, next_label = self.new_label("salir"), self.new_label("sigue")
        self.emit(f"block {exit_label}")
        self.emit(f"loop {next_label}")
        with self.indented():
            if condition is not None:
                self.visit(condition)
                self.emit("i32.eqz")
                self.emit(f"br_if {exit_label}")
            self.fn.loops.append((exit_label, next_label))
            self.visit(body)
            self.fn.loops.pop()
            self.emit(f"br {next_label}")
        self.emit("end")
        self.emit("end")

    # --- break / continue / return -------------------------------------------

    def visitBreakStmt(self, ctx: P.BreakStmtContext):
        self.emit(f"br {self.fn.loops[-1][0]}")

    def visitContinueStmt(self, ctx: P.ContinueStmtContext):
        self.emit(f"br {self.fn.loops[-1][1]}")

    def visitReturnStmt(self, ctx: P.ReturnStmtContext):
        if ctx.expression() is not None:
            self.visit(ctx.expression())
        self.emit("return")

    # --- const local --------------------------------------------------------------

    def visitConstLocalDecl(self, ctx: P.ConstLocalDeclContext):
        symbol = self.info.symbol.get(ctx)
        self.declare_symbol(symbol)
        self.store_symbol(symbol, lambda: self.visit(ctx.expression()))
