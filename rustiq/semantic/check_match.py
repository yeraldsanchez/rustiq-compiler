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
from rustiq.semantic.info import EnumDef
from rustiq.types import BOOL, EnumT, TupleT, Type, is_copy


class MatchMixin:
    # --- Enum::Variante(args) -------------------------------------------------

    def visitEnumValue(self, ctx: P.EnumValueContext):
        enum_name, variant = ctx.IDENT(0).getText(), ctx.IDENT(1).getText()
        args = ctx.argumentList().expression() if ctx.argumentList() is not None else []
        arg_types = [self.visit(a) for a in args]  # siempre, para ver sus errores
        for a in args:
            self.consume(a)
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
        scrutinee = self.reject_unit(ctx.condition(), self.visit(ctx.condition()), "El valor de match")
        if scrutinee is None:
            return None
        self.info.expr_type.put(ctx.condition(), scrutinee)
        result, patterns_ok = None, True
        before, branches = self.branch_start(), []
        for arm in ctx.matchArm():
            self.info.expr_type.put(arm.pattern(), scrutinee)
            self.branch_restore(before)
            self.push_scope()  # los bindings de un brazo solo existen en ese brazo
            pattern_ok = self.visit(arm.pattern()) is not None
            body = self.visit(arm.expression()) if pattern_ok else None
            if pattern_ok:
                self.consume(arm.expression())
            self.pop_scope()
            branches.append(self.move_states)
            patterns_ok = patterns_ok and pattern_ok
            if result is None:
                result = body
            else:
                self.mismatch(arm.expression(), E_TYPE_MISMATCH, result, body, "El brazo de match")
        self.branch_end(before, branches)
        if binds_owned_value(self.info, [arm.pattern() for arm in ctx.matchArm()]):
            self.consume(ctx.condition())
        if patterns_ok and not is_exhaustive([arm.pattern() for arm in ctx.matchArm()], scrutinee, self.info.enums):
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
        self.track_symbol(symbol)
        return expected

    def visitLiteralPat(self, ctx: P.LiteralPatContext):
        expected = self.info.expr_type.get(ctx)
        if ctx.literal().STRING_LIT() is not None:
            self.error(ctx, E_BAD_PATTERN, "Un String no se puede usar como patrón")
            return None
        if self.mismatch(ctx, E_TYPE_MISMATCH, expected, self.visit(ctx.literal()), "El patrón"):
            return None
        return expected

    def visitTuplePat(self, ctx: P.TuplePatContext):
        expected = self.info.expr_type.get(ctx)
        subs = ctx.pattern()
        if not isinstance(expected, TupleT):
            self.error(ctx, E_BAD_PATTERN, f"Un patrón de tupla no sirve para un valor de tipo {expected}")
            return None
        if len(subs) != len(expected.elems):
            self.error(
                ctx, E_TYPE_MISMATCH,
                f"El patrón tiene {len(subs)} elementos y la tupla {expected} tiene {len(expected.elems)}",
            )
            return None
        return expected if self._check_sub_patterns(subs, expected.elems) else None

    def visitEnumPat(self, ctx: P.EnumPatContext):
        expected = self.info.expr_type.get(ctx)
        enum_name, variant = ctx.IDENT(0).getText(), ctx.IDENT(1).getText()
        subs = _enum_sub_patterns(ctx)
        payload = self._variant_payload(ctx, enum_name, variant)
        if payload is None:
            return None
        if not isinstance(expected, EnumT):
            self.error(ctx, E_BAD_PATTERN, f"Un patrón de enum no sirve para un valor de tipo {expected}")
            return None
        if self.mismatch(ctx, E_TYPE_MISMATCH, expected, EnumT(enum_name), "El patrón"):
            return None
        if len(subs) != len(payload):
            self.error(
                ctx, E_ARG_COUNT,
                f"'{enum_name}::{variant}' tiene {len(payload)} dato(s) y el patrón {len(subs)}",
            )
            return None
        return expected if self._check_sub_patterns(subs, payload) else None

    def _check_sub_patterns(self, subs: list[P.PatternContext], types) -> bool:
        """Revisa cada subpatrón contra su tipo. True si todos son válidos."""
        ok = True
        for sub, sub_type in zip(subs, types):
            self.info.expr_type.put(sub, sub_type)
            ok = self.visit(sub) is not None and ok
        return ok


# --- Exhaustividad (decisión G10) ---------------------------------------------


def is_irrefutable(pattern: P.PatternContext) -> bool:
    """True si el patrón calza con cualquier valor de su tipo."""
    if isinstance(pattern, P.TuplePatContext):
        return all(is_irrefutable(sub) for sub in pattern.pattern())
    return isinstance(pattern, (P.WildcardPatContext, P.BindingPatContext))


def is_exhaustive(patterns: list[P.PatternContext], scrutinee: Type, enums: dict[str, EnumDef]) -> bool:
    if any(is_irrefutable(p) for p in patterns):
        return True
    if isinstance(scrutinee, EnumT):
        covered = {
            p.IDENT(1).getText()
            for p in patterns
            if isinstance(p, P.EnumPatContext) and all(is_irrefutable(sub) for sub in _enum_sub_patterns(p))
        }
        return covered >= set(enums[scrutinee.name].variants)
    if scrutinee == BOOL:
        texts = {p.getText() for p in patterns if isinstance(p, P.LiteralPatContext)}
        return {"true", "false"} <= texts
    return False


def _enum_sub_patterns(pattern: P.EnumPatContext) -> list[P.PatternContext]:
    return pattern.patternList().pattern() if pattern.patternList() is not None else []


def binds_owned_value(info, patterns: list[P.PatternContext]) -> bool:
    """True si algún patrón liga un valor que no es Copy; solo así el match mueve su valor."""
    pending = list(patterns)
    while pending:
        node = pending.pop()
        if isinstance(node, P.BindingPatContext):
            symbol = info.symbol.get(node)
            if symbol is not None and not is_copy(symbol.type):
                return True
        pending.extend(c for c in (node.children or []) if isinstance(c, P.PatternContext) or isinstance(c, P.PatternListContext))
    return False
