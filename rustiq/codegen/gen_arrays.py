"""Generación de código de arrays.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos. Lo implementó A con su permiso.

Layout (docs/memoria.md): un array es un puntero a `n` ranuras de 8 bytes, igual
que una tupla. Cada acceso revisa el índice al ejecutar y hace `unreachable` si
se sale.
"""

from rustiq.codegen.gen_structs import SLOT_SIZE
from rustiq.codegen.wasm_types import wasm_type
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.types import I32, ArrayT, RefT, Type


def array_of(operand: Type) -> ArrayT:
    """El array detrás de `operand`, quitando un nivel de referencia."""
    return operand.target if isinstance(operand, RefT) else operand


class ArraysGenMixin:
    def visitArrayP(self, ctx: P.ArrayPContext):
        self.visit(ctx.arrayLiteral())

    def visitArrayLiteral(self, ctx: P.ArrayLiteralContext):
        array = self.info.expr_type.get(ctx)
        pointer = self.alloc_slots(array.size)
        for index, element in enumerate(ctx.expression()):
            self.store_slot(pointer, index, array.elem, element)
        self.emit(f"local.get {pointer}")

    def visitIndexSuffix(self, ctx: P.IndexSuffixContext):
        array = array_of(self.info.expr_type.get(ctx))
        self.emit_element_address(ctx.expression(), array.size)
        self.emit(f"{wasm_type(array.elem)}.load")

    def emit_element_address(self, index, size: int) -> None:
        """Con el puntero del array en la pila, deja la dirección de `array[index]`."""
        base = self.new_pointer_temp()
        position = self.new_temp(I32)
        self.emit(f"local.set {base}")
        self.visit(index)
        self.emit(f"local.set {position}")
        # Sin signo, un índice negativo también queda fuera de rango
        self.emit(f"local.get {position}")
        self.emit(f"i32.const {size}")
        self.emit("i32.ge_u")
        self.emit("if")
        with self.indented():
            self.emit("unreachable")
        self.emit("end")
        self.emit(f"local.get {base}")
        self.emit(f"local.get {position}")
        self.emit(f"i32.const {SLOT_SIZE}")
        self.emit("i32.mul")
        self.emit("i32.add")
