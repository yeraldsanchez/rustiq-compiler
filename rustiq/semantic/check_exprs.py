"""Comprobación de tipos de expresiones y operadores (Carril B)."""

from rustiq.errors import E_BORROW_CONFLICT, E_BORROW_MUT_IMMUTABLE
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.types import BOOL, CHAR, F64, I32, RefT, String


class ExprsMixin:
    def visitLiteral(self, ctx: P.LiteralContext):
        if ctx.STRING_LIT() is not None:
            return String
        if ctx.INT_LIT() is not None:
            return I32
        if ctx.FLOAT_LIT() is not None:
            return F64
        if ctx.CHAR_LIT() is not None:
            return CHAR
        return BOOL

    def visitUnary(self, ctx):
        inner = self.visit(ctx.postfix())
        if inner is not None:
            self.info.expr_type.put(ctx.postfix(), inner)
        if ctx.AMP() is not None:
            target_name = None
            primary = ctx.postfix().primary()
            if isinstance(primary, P.IdentPContext):
                target_name = primary.IDENT().getText()
            symbol = self.lookup(target_name) if target_name else None
            is_mut = ctx.MUT() is not None
            if symbol is not None:
                if is_mut:
                    if not symbol.mutable:
                        self.error(ctx, E_BORROW_MUT_IMMUTABLE, f"'{symbol.name}' es inmutable y no puede recibir &mut")
                    elif self.is_borrowed(symbol):
                        self.error(ctx, E_BORROW_CONFLICT, f"'{symbol.name}' ya está prestado y no puede recibir &mut")
                    else:
                        self.borrow_mutable(symbol)
                else:
                    if self.is_mutably_borrowed(symbol):
                        self.error(ctx, E_BORROW_CONFLICT, f"'{symbol.name}' tiene préstamo mutable; no se puede crear &")
                    else:
                        self.borrow_shared(symbol)
            return RefT(inner, is_mut) if inner is not None else None
        if ctx.STAR() is not None:
            return inner.target if isinstance(inner, RefT) else None
        if ctx.BANG() is not None:
            return BOOL if inner is not None else None
        return inner
