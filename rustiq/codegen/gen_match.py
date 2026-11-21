"""Generación de código de enums y match.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos.

Layout (docs/memoria.md): un enum es un puntero a `[tag][payload...]`. El tag
ocupa la ranura 0 completa y cada dato del payload una ranura desde la 1.

Un match guarda su valor en un temporal y abre un `block` por brazo. Si el patrón
no calza, se salta al final de ese bloque y se prueba el siguiente brazo. Si
calza, se evalúa el cuerpo y se salta a la salida del match. Después del último
brazo va `unreachable`: el análisis de exhaustividad garantiza que no se llega.
"""

from rustiq.codegen.gen_structs import slot_offset
from rustiq.codegen.wasm_types import wasm_type
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.types import UNIT

class MatchGenMixin:
    # --- Enum::Variante(args) -------------------------------------------------

    def visitEnumP(self, ctx: RustiQParser.EnumPContext):
        self.visit(ctx.enumValue())

    def visitEnumValue(self, ctx: RustiQParser.EnumValueContext):
        definition = self.info.enums[ctx.IDENT(0).getText()]
        variant = ctx.IDENT(1).getText()
        payload = definition.variants[variant]
        args = ctx.argumentList().expression() if ctx.argumentList() is not None else []
        
        # Usamos _alloc_slots de tu gen_structs.py (1 slot para tag + payload)
        pointer = self._alloc_slots(1 + len(payload))
        self.emit(f"local.get {pointer}")
        self.emit(f"i32.const {list(definition.variants.keys()).index(variant)}")
        self.emit(f"i32.store offset={slot_offset(0)}")
        
        # Usamos _store_slot de tu gen_structs.py
        for i, (value_type, arg) in enumerate(zip(payload, args)):
            self._store_slot(pointer, 1 + i, value_type, arg)
        self.emit(f"local.get {pointer}")

    # --- match ------------------------------------------------------------------

    def visitMatchExpr(self, ctx: RustiQParser.MatchExprContext):
        result = self.info.expr_type.get(ctx)
        value = self.new_temp(self.info.expr_type.get(ctx.condition()))
        self.visit(ctx.condition())
        self.emit(f"local.set {value}")
        exit_label = self.new_label("fin_match")
        result_part = f" (result {wasm_type(result)})" if result != UNIT else ""
        self.emit(f"block {exit_label}{result_part}")
        self._depth += 1
        for arm in ctx.matchArm():
            next_arm = self.new_label("sig_brazo")
            self.emit(f"block {next_arm}")
            self._depth += 1
            self.gen_pattern(arm.pattern(), value, next_arm)
            self.visit(arm.expression())
            self.emit(f"br {exit_label}")
            self._depth -= 1
            self.emit("end")
        self.emit("unreachable")
        self._depth -= 1
        self.emit("end")

    # --- Patrones ---------------------------------------------------------------

    def gen_pattern(self, pattern: RustiQParser.PatternContext, value: str, fail: str) -> None:
        """Prueba `pattern` contra el valor del local `value`.

        Si no calza salta a `fail`; si calza asigna sus bindings. No deja nada en la pila.
        """
        value_type = self.info.expr_type.get(pattern)
        if isinstance(pattern, RustiQParser.BindingPatContext):
            name = self.declare_symbol(self.info.symbol.get(pattern))
            self.emit(f"local.get {value}")
            self.emit(f"local.set {name}")
        elif isinstance(pattern, RustiQParser.LiteralPatContext):
            self.emit(f"local.get {value}")
            self.visit(pattern.literal())
            self.emit(f"{wasm_type(value_type)}.ne")
            self.emit(f"br_if {fail}")
        elif isinstance(pattern, RustiQParser.TuplePatContext):
            for slot, sub in enumerate(pattern.pattern()):
                self._gen_slot_pattern(value, slot, sub, fail)

        elif isinstance(pattern, RustiQParser.EnumPatContext):
            definition = self.info.enums[pattern.IDENT(0).getText()]
            self.emit(f"local.get {value}")
            self.emit(f"i32.load offset={slot_offset(0)}")
            self.emit(f"i32.const {list(definition.variants.keys()).index(pattern.IDENT(1).getText())}")
            self.emit("i32.ne")
            self.emit(f"br_if {fail}")
            subs = pattern.patternList().pattern() if pattern.patternList() is not None else []
            for i, sub in enumerate(subs):
                self._gen_slot_pattern(value, 1 + i, sub, fail)

    def _gen_slot_pattern(self, pointer: str, slot: int, pattern: RustiQParser.PatternContext, fail: str) -> None:
        """Carga la ranura `slot` del bloque en `pointer` y le prueba `pattern`."""
        if isinstance(pattern, RustiQParser.WildcardPatContext):
            return
        slot_type = self.info.expr_type.get(pattern)
        temp = self.new_temp(slot_type)
        self.emit(f"local.get {pointer}")
        self.emit(f"{wasm_type(slot_type)}.load offset={slot_offset(slot)}")
        self.emit(f"local.set {temp}")
        self.gen_pattern(pattern, temp, fail)