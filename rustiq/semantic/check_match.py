"""Enums y match: patrones, tipos de los brazos y exhaustividad.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas; si necesita algo de
otro mixin, llama su método público y nunca copia la lógica.
"""

from rustiq.errors import (
    E_ARG_COUNT,
    E_BAD_PATTERN,
    E_NOT_EXHAUSTIVE,
    E_TYPE_MISMATCH,
    E_UNKNOWN_TYPE,
    E_UNKNOWN_VARIANT,
)
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.types import BOOL, EnumT, Type


class MatchMixin:
    # --- Enum::Variante(args) -------------------------------------------------

    def visitEnumValue(self, ctx: P.EnumValueContext):
        enum_name, variant = ctx.IDENT(0).getText(), ctx.IDENT(1).getText()
        args = ctx.argumentList().expression() if ctx.argumentList() is not None else []
        arg_types = [self.visit(a) for a in args]  # siempre, para ver sus errores
        payload = self._variant_payload(ctx, enum_name, variant)
        if payload is None:
            return None
        if len(args) != len(payload):
            self.error(
                ctx, E_ARG_COUNT,
                f"'{enum_name}::{variant}' espera {len(payload)} dato(s) y recibió {len(args)}",
            )
        else:
            for i, (arg, expected, actual) in enumerate(zip(args, payload, arg_types), 1):
                self.mismatch(arg, E_TYPE_MISMATCH, expected, actual, f"El dato {i} de '{enum_name}::{variant}'")
        result = EnumT(enum_name)
        self.info.expr_type.put(ctx, result)
        return result

    def _variant_payload(self, ctx, enum_name: str, variant: str):
        """Tipos del payload de `Enum::Variante`, o None si el enum o la variante no existen."""
        definition = self.info.enums.get(enum_name)
        if definition is None:
            self.error(ctx.IDENT(0), E_UNKNOWN_TYPE, f"El enum '{enum_name}' no existe")
            return None
        if variant not in definition.variants:
            self.error(ctx.IDENT(1), E_UNKNOWN_VARIANT, f"'{enum_name}' no tiene la variante '{variant}'")
            return None
        return definition.variants[variant]

    # --- match ------------------------------------------------------------------

    def visitMatchExpr(self, ctx: P.MatchExprContext):
        scrutinee = self.visit(ctx.condition())
        if scrutinee is None:
            return None
        self.info.expr_type.put(ctx.condition(), scrutinee)
        result, patterns_ok = None, True
        for arm in ctx.matchArm():
            self.info.expr_type.put(arm.pattern(), scrutinee)
            self.push_scope()  # los bindings de un brazo solo existen en ese brazo
            pattern_ok = self.visit(arm.pattern()) is not None
            body = self.visit(arm.expression()) if pattern_ok else None
            self.pop_scope()
            patterns_ok = patterns_ok and pattern_ok
            if result is None:
                result = body
            else:
                self.mismatch(arm.expression(), E_TYPE_MISMATCH, result, body, "El brazo de match")
        if patterns_ok and not is_exhaustive([arm.pattern() for arm in ctx.matchArm()], scrutinee):
            self.error(ctx.MATCH(), E_NOT_EXHAUSTIVE, f"El match sobre {scrutinee} no cubre todos los casos; agrega un brazo '_'")
        if result is not None:
            self.info.expr_type.put(ctx, result)
        return result

    # --- Patrones ---------------------------------------------------------------
    #
    # El padre pone en `info.expr_type[patrón]` el tipo del valor que se prueba.
    # Cada visitXPat devuelve ese tipo si el patrón es válido, o None si reportó un error.

    def visitWildcardPat(self, ctx: P.WildcardPatContext):
        return self.info.expr_type.get(ctx)

    def visitBindingPat(self, ctx: P.BindingPatContext):
        expected = self.info.expr_type.get(ctx)
        symbol = self.declare(ctx.IDENT().getText(), expected, False, "local", ctx.IDENT())
        if symbol is None:
            return None
        self.info.symbol.put(ctx, symbol)
        return expected

    def visitLiteralPat(self, ctx: P.LiteralPatContext):
        expected = self.info.expr_type.get(ctx)
        if ctx.literal().STRING_LIT() is not None:
            self.error(ctx, E_BAD_PATTERN, "Un String no se puede usar como patrón")
            return None
        if self.mismatch(ctx, E_TYPE_MISMATCH, expected, self.visit(ctx.literal()), "El patrón"):
            return None
        return expected


# --- Exhaustividad (decisión G10) ---------------------------------------------


def is_irrefutable(pattern: P.PatternContext) -> bool:
    """True si el patrón calza con cualquier valor de su tipo."""
    return isinstance(pattern, (P.WildcardPatContext, P.BindingPatContext))


def is_exhaustive(patterns: list[P.PatternContext], scrutinee: Type) -> bool:
    if any(is_irrefutable(p) for p in patterns):
        return True
    if scrutinee == BOOL:
        texts = {p.getText() for p in patterns if isinstance(p, P.LiteralPatContext)}
        return {"true", "false"} <= texts
    return False
