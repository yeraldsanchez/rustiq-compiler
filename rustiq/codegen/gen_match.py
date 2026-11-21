"""Generación de código de enums y match.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos.
"""

from rustiq.generated.RustiQParser import RustiQParser
from rustiq.codegen.wasm_types import wasm_type
from rustiq.types import F64, I32


class MatchGenMixin:
    def visitEnumP(self, ctx: RustiQParser.EnumPContext):
        """Un enum en una expresión principal (ej. al pasarlo como argumento)."""
        self.visit(ctx.enumValue())

    def visitEnumValue(self, ctx: RustiQParser.EnumValueContext):
        """Genera el código para crear una variante de enum (ej. Forma::Cuadrado(7))."""
        enum_name = ctx.IDENT(0).getText()
        variant_name = ctx.IDENT(1).getText()

        enum_def = self.info.enums[enum_name]
        tag = list(enum_def.variants.keys()).index(variant_name)
        payload_types = enum_def.variants[variant_name]

        # 1 slot (8 bytes) para el tag, y un slot por cada dato del payload
        size = 8 * (1 + len(payload_types))
        self.emit(f"i32.const {size}")
        self.emit("call $alloc")
        tmp = self.new_temp(I32)
        self.emit(f"local.set {tmp}")

        # Guardar el tag en el offset 0
        self.emit(f"local.get {tmp}")
        self.emit(f"i32.const {tag}")
        self.emit("i32.store")

        # Guardar los argumentos si tiene payload
        if ctx.argumentList():
            args = ctx.argumentList().expression()
            for i, (arg, ptype) in enumerate(zip(args, payload_types)):
                self.emit(f"local.get {tmp}")
                self.visit(arg)
                offset = 8 * (i + 1)
                self.emit(f"{wasm_type(ptype)}.store offset={offset}")

        # Dejar el puntero al enum en la pila
        self.emit(f"local.get {tmp}")

    def visitMatchExpr(self, ctx: RustiQParser.MatchExprContext):
        # Evaluar la condición (deja un puntero en la pila)
        self.visit(ctx.condition())
        cond_tmp = self.new_temp(I32)
        self.emit(f"local.set {cond_tmp}")
        
        res_type = self.info.expr_type.get(ctx)
        res_tmp = self.new_temp(res_type)
        
        label = self.new_label("match")
        self.emit(f"block {label}")
        
        for arm in ctx.matchArm():
            self._bind_pattern(arm.pattern(), cond_tmp, 0)
            self.visit(arm.expression())
            self.emit(f"local.set {res_tmp}")
            self.emit(f"br {label}")
            
        self.emit("end")
        self.emit(f"local.get {res_tmp}")
        
    def _bind_pattern(self, pat, base_ptr, offset):
        if isinstance(pat, RustiQParser.BindingPatContext):
            sym = self.info.symbol.get(pat)
            if sym:
                lname = self.local_name(sym)
                self.declare_local(lname, sym.type)
                self.emit(f"local.get {base_ptr}")
                if offset > 0:
                    self.emit(f"i32.const {offset}")
                    self.emit("i32.add")
                self.emit("f64.load" if sym.type == F64 else "i32.load")
                self.emit(f"local.set {lname}")
        elif isinstance(pat, RustiQParser.TuplePatContext):
            for i, sub_pat in enumerate(pat.pattern()):
                self._bind_pattern(sub_pat, base_ptr, offset + i * 8)
        elif isinstance(pat, RustiQParser.EnumPatContext):
            if pat.patternList():
                # El tag está en offset 0, el payload empieza en el offset 8
                payload_offset = offset + 8
                for i, sub_pat in enumerate(pat.patternList().pattern()):
                    self._bind_pattern(sub_pat, base_ptr, payload_offset + i * 8)