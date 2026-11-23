"""Generación de código de structs y tuplas.

Lee `SemanticInfo` y nunca vuelve a inferir tipos.

Layout (docs/memoria.md): un struct o tupla es un puntero a sus campos en orden
de declaración, cada uno en una ranura de 8 bytes. Un campo struct o tupla guarda
el puntero a su propio bloque. Una referencia a un struct es el mismo puntero,
así que acceder por `&T` no necesita cargar nada extra.
"""

from rustiq.codegen.wasm_types import wasm_type
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.types import RefT, StructT, Type

SLOT_SIZE = 8
TAG_SLOT = 0  # un enum guarda su tag en la ranura 0
PAYLOAD_FIRST_SLOT = 1  # y su payload desde la ranura 1


def slot_offset(index: int) -> int:
    return SLOT_SIZE * index


class StructsGenMixin:
    def field_slot(self, struct_type: Type, field: str) -> tuple[int, Type]:
        """(posición de la ranura, tipo del campo). Acepta `T` y `&T` / `&mut T`."""
        base = struct_type.target if isinstance(struct_type, RefT) else struct_type
        assert isinstance(base, StructT)
        fields = self.info.structs[base.name].fields
        return list(fields).index(field), fields[field]

    def alloc_slots(self, count: int) -> str:
        """Reserva `count` ranuras y deja el puntero en un local temporal nuevo."""
        pointer = self.new_pointer_temp()
        self.emit(f"i32.const {slot_offset(count)}")
        self.emit("call $alloc")
        self.emit(f"local.set {pointer}")
        return pointer

    def store_slot(self, pointer: str, index: int, value_type: Type, expression) -> None:
        self.emit(f"local.get {pointer}")
        self.visit(expression)
        self.emit(f"{wasm_type(value_type)}.store offset={slot_offset(index)}")

    def visitStructLiteral(self, ctx: P.StructLiteralContext):
        fields = self.info.structs[ctx.IDENT().getText()].fields
        pointer = self.alloc_slots(len(fields))
        for init in ctx.fieldInit():  # se evalúan en el orden en que se escribieron
            name = init.IDENT().getText()
            self.store_slot(pointer, list(fields).index(name), fields[name], init.expression())
        self.emit(f"local.get {pointer}")

    def visitTupleLiteral(self, ctx: P.TupleLiteralContext):
        elems = self.info.expr_type.get(ctx).elems
        pointer = self.alloc_slots(len(elems))
        for index, (elem_type, expression) in enumerate(zip(elems, ctx.expression())):
            self.store_slot(pointer, index, elem_type, expression)
        self.emit(f"local.get {pointer}")

    def visitFieldSuffix(self, ctx: P.FieldSuffixContext):
        index, field_type = self.field_slot(self.info.expr_type.get(ctx), ctx.IDENT().getText())
        self.emit(f"{wasm_type(field_type)}.load offset={slot_offset(index)}")
