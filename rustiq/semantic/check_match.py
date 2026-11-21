"""Enums y match: patrones, tipos de los brazos y exhaustividad.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas; si necesita algo de
otro mixin, llama su método público y nunca copia la lógica.
"""

from rustiq.errors import E_ARG_COUNT, E_TYPE_MISMATCH, E_UNKNOWN_TYPE, E_UNKNOWN_VARIANT
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.types import EnumT


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
