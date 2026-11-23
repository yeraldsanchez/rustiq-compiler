"""Asignación: `=`, `+=`, `-=`, `*=`, `/=` sobre un `place`.

Dueño: B (Byron). Lo implementó A con su permiso para cerrar movimientos.

Va después de `BorrowsMixin` en la herencia: `BorrowsMixin.visitAssignment`
revisa el préstamo activo y llama a este con `super()`.

Reglas:
- Solo se asigna a variables `mut`. La excepción es la primera asignación de
  un `let x: T;` sin inicializador.
- Con `p.campo = v` basta con que `p` sea `mut` o una `&mut`.
- `+=` y compañía solo sobre `i32` y `f64`, y leen el valor anterior.
- `x = v` mueve `v` y deja `x` disponible otra vez (reinicialización).
"""

from rustiq.errors import E_ASSIGN_IMMUTABLE, E_BAD_OPERAND, E_TYPE_MISMATCH, E_UNDECLARED, E_UNKNOWN_FIELD
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.semantic.info import VARIABLE_KINDS
from rustiq.semantic.moves import UNINITIALIZED
from rustiq.tree import place_accessors
from rustiq.types import F64, I32, RefT, StructT, Type

NUMERIC = (I32, F64)


class AssignMixin:
    def visitAssignment(self, ctx: P.AssignmentContext):
        place = ctx.place()
        root = place.IDENT(0)
        value = self.visit(ctx.expression())
        symbol = self.lookup(root.getText())
        if symbol is None:
            self.error(root, E_UNDECLARED, f"Identificador '{root.getText()}' no declarado")
            return None
        self.info.symbol.put(ctx, symbol)

        op = ctx.assignOp().getText()
        whole = place.getChildCount() == 1  # `x = ...`, sin campos ni índices
        if not (whole and op == "="):
            self.check_use(symbol, root)  # se lee el valor anterior o una parte
        self._check_mutable(symbol, root, whole and op == "=")

        target = self._place_type(place, symbol.type)
        if target is not None:
            self._check_value(ctx, op, target, value)
        if op == "=":
            self.consume(ctx.expression())
            if whole:
                self.mark_initialized(symbol)
                if isinstance(symbol.type, RefT):
                    self.track_ref_origin(symbol, ctx.expression())
        return None

    def _check_mutable(self, symbol, root, replaces_whole: bool) -> None:
        if symbol.kind not in VARIABLE_KINDS:
            self.error(root, E_ASSIGN_IMMUTABLE, f"No se puede asignar a '{symbol.name}'")
        elif symbol.mutable:
            return
        elif replaces_whole and self.move_state(symbol) == UNINITIALIZED:
            return  # primera asignación de `let x: T;`
        elif not replaces_whole and isinstance(symbol.type, RefT) and symbol.type.mutable:
            return  # `p.campo = v` con `p: &mut T`
        else:
            self.error(root, E_ASSIGN_IMMUTABLE, f"'{symbol.name}' no es mut y no se puede asignar")

    def _place_type(self, place: P.PlaceContext, current: Type | None) -> Type | None:
        """Tipo de lo que se asigna, recorriendo los campos e índices del `place`."""
        for field, index in place_accessors(place):
            if current is None:
                break
            current = self._field_type(current, field) if field is not None else self.index_type(current, index)
        return current

    def _field_type(self, operand: Type, ident) -> Type | None:
        base = operand.target if isinstance(operand, RefT) else operand
        name = ident.getText()
        if not isinstance(base, StructT):
            self.error(ident, E_BAD_OPERAND, f"El tipo {operand} no tiene campos")
            return None
        fields = self.info.structs[base.name].fields
        if name not in fields:
            self.error(ident, E_UNKNOWN_FIELD, f"'{base.name}' no tiene el campo '{name}'")
            return None
        return fields[name]

    def _check_value(self, ctx, op: str, target: Type, value: Type | None) -> None:
        if op != "=" and target not in NUMERIC:
            self.error(ctx.assignOp(), E_BAD_OPERAND, f"'{op}' solo se usa con i32 o f64, no con {target}")
            return
        if value is not None:
            self.info.expr_type.put(ctx.expression(), value)
        self.mismatch(ctx.expression(), E_TYPE_MISMATCH, target, value, "El valor asignado")
