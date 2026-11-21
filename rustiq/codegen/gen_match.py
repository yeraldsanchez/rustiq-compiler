"""Generación de código de enums y match.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos.

Layout (docs/memoria.md): un enum es un puntero a `[tag][payload...]`. El tag
ocupa la ranura 0 completa y cada dato del payload una ranura desde la 1.
"""

from rustiq.codegen.gen_structs import PAYLOAD_FIRST_SLOT, TAG_SLOT, slot_offset
from rustiq.generated.RustiQParser import RustiQParser as P


class MatchGenMixin:
    # --- Enum::Variante(args) -------------------------------------------------

    def visitEnumValue(self, ctx: P.EnumValueContext):
        definition = self.info.enums[ctx.IDENT(0).getText()]
        variant = ctx.IDENT(1).getText()
        payload = definition.variants[variant]
        args = ctx.argumentList().expression() if ctx.argumentList() is not None else []
        pointer = self.alloc_slots(PAYLOAD_FIRST_SLOT + len(payload))
        self.emit(f"local.get {pointer}")
        self.emit(f"i32.const {definition.tag_of(variant)}")
        self.emit(f"i32.store offset={slot_offset(TAG_SLOT)}")
        for i, (value_type, arg) in enumerate(zip(payload, args)):
            self.store_slot(pointer, PAYLOAD_FIRST_SLOT + i, value_type, arg)
        self.emit(f"local.get {pointer}")
