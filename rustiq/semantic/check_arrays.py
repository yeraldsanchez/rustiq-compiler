"""Arrays: literales, indexado y tamaño.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas; si necesita algo de
otro mixin, llama su método público y nunca copia la lógica. Lo implementó A
con su permiso.

- `[a, b, c]` tiene tipo `[T; 3]` si todos los elementos son `T`. Cada
  elemento se mueve al array.
- `a[i]` necesita un array (o una referencia a uno) y un índice `i32`. Un
  índice literal fuera de rango es error de compilación; uno calculado se
  revisa al ejecutar (`unreachable`).
"""

from rustiq.errors import E_BAD_INDEX, E_TYPE_MISMATCH
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.types import I32, ArrayT, RefT, Type


class ArraysMixin:
    def visitArrayP(self, ctx: P.ArrayPContext):
        return self.visit(ctx.arrayLiteral())

    def visitArrayLiteral(self, ctx: P.ArrayLiteralContext):
        elements = ctx.expression()
        types = [self.reject_unit(e, self.visit(e), "Un elemento de array") for e in elements]
        for element in elements:
            self.consume(element)
        first = types[0]
        if first is None:
            return None
        for element, t in zip(elements[1:], types[1:]):
            if self.mismatch(element, E_TYPE_MISMATCH, first, t, "Elemento del array"):
                return None
        if any(t is None for t in types):
            return None
        result = ArrayT(first, len(elements))
        self.info.expr_type.put(ctx, result)
        return result

    def visitIndexSuffix(self, ctx: P.IndexSuffixContext):
        operand = self.info.expr_type.get(ctx)
        return self.index_type(operand, ctx.expression())

    def index_type(self, operand: Type, index) -> Type | None:
        """Tipo del elemento de `operand[index]`. Lo usa también la asignación."""
        index_type = self.visit(index)
        if index_type is not None:
            self.info.expr_type.put(index, index_type)
        self.mismatch(index, E_TYPE_MISMATCH, I32, index_type, "El índice")
        array = operand.target if isinstance(operand, RefT) else operand  # auto-deref de un nivel
        if not isinstance(array, ArrayT):
            self.error(index, E_BAD_INDEX, f"El tipo {operand} no se puede indexar")
            return None
        literal = index.getText()
        if literal.isdigit() and int(literal) >= array.size:
            self.error(index, E_BAD_INDEX, f"El índice {literal} está fuera de un array de {array.size}")
            return None
        return array.elem
