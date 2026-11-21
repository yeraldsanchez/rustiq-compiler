"""Comprobación de tipos de expresiones y operadores (Carril B)."""

from rustiq.types import BOOL, RefT


class ExprsMixin:
    def visitUnary(self, ctx):
        inner = self.visit(ctx.postfix())
        if inner is not None:
            self.info.expr_type.put(ctx.postfix(), inner)
        if ctx.AMP() is not None:
            return RefT(inner, ctx.MUT() is not None) if inner is not None else None
        if ctx.STAR() is not None:
            return inner.target if isinstance(inner, RefT) else None
        if ctx.BANG() is not None:
            return BOOL if inner is not None else None
        return inner