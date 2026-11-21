"""Generación de código de arrays.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos.
"""

from rustiq.generated.RustiQParser import RustiQParser
from rustiq.types import I32, F64, ArrayT


class ArraysGenMixin:
    def visitArrayP(self, ctx: RustiQParser.ArrayPContext):
        self.visit(ctx.arrayLiteral())

    def visitArrayLiteral(self, ctx: RustiQParser.ArrayLiteralContext):
        elements = ctx.expression()
        n = len(elements)
        
        # Todos los elementos ocupan 8 bytes en memoria (i32 o f64)
        self.emit(f"i32.const {n * 8}")
        self.emit("call $alloc")
        tmp = self.new_temp(I32)
        self.emit(f"local.set {tmp}")

        arr_type = self.info.expr_type.get(ctx)
        elem_type = arr_type.elem if isinstance(arr_type, ArrayT) else I32

        for i, elem in enumerate(elements):
            self.emit(f"local.get {tmp}")
            if i > 0:
                self.emit(f"i32.const {i * 8}")
                self.emit("i32.add")
            
            self.visit(elem)
            
            self.emit("f64.store" if elem_type == F64 else "i32.store")

        # Dejar el puntero al inicio del array en la pila
        self.emit(f"local.get {tmp}")

    def visitIndexSuffix(self, ctx: RustiQParser.IndexSuffixContext):
        # En la pila ya está la dirección base del array.
        tmp_base = self.new_temp(I32)
        self.emit(f"local.set {tmp_base}")

        # Evaluar el índice
        self.visit(ctx.expression())
        self.emit("i32.const 8")
        self.emit("i32.mul")

        # sumar base
        self.emit(f"local.get {tmp_base}")
        self.emit("i32.add")

        # Cargar el valor (averiguamos el tipo)
        # En IndexSuffixContext, el info.expr_type ya contiene el tipo del resultado
        elem_type = self.info.expr_type.get(ctx)
        self.emit("f64.load" if elem_type == F64 else "i32.load")