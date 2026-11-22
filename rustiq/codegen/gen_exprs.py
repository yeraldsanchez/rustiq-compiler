"""Generación de código de literales, operadores y variables.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos.
"""

from rustiq.generated.RustiQParser import RustiQParser


class ExprsGenMixin:
    def visitLetDecl(self, ctx: RustiQParser.LetDeclContext):
        symbol = self.info.symbol.get(ctx)
        if symbol is not None:
            lname = self.declare_symbol(symbol)
            if ctx.expression() is not None:
                self.visit(ctx.expression())
                self.emit(f"local.set {lname}")

    def visitIdentP(self, ctx: RustiQParser.IdentPContext):
        symbol = self.info.symbol.get(ctx)
        if symbol is not None:
            self.load_symbol(symbol)
