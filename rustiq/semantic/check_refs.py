"""Referencias (`&`, `&mut`, `*`) y literales de String (Carril B)."""

from rustiq.errors import E_BAD_OPERAND
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.types import BOOL, CHAR, F64, I32, RefT, Type

SCALAR_TYPES = (I32, F64, BOOL, CHAR)


class RefsMixin:
    def check_borrow_operand(self, unary_ctx: RustiQParser.UnaryContext) -> Type | None:
        """Valida `&postfix` y `&mut postfix`, marca `address_taken` y registra el préstamo."""
        postfix = unary_ctx.postfix()
        is_mut = unary_ctx.MUT() is not None
        inner_type = self.visit(postfix)
        if inner_type is None:
            return None

        self.info.expr_type.put(postfix, inner_type)

        # Extraer el símbolo base del postfix (identificador, campo o índice)
        root_name = self._extract_root_ident(postfix)
        if root_name is None and isinstance(postfix.primary(), RustiQParser.IdentPContext):
            root_name = postfix.primary().IDENT().getText()

        symbol = self.lookup(root_name) if root_name is not None else None
        if symbol is not None:
            # Si es escalar y se toma su dirección directamente (&x o &mut x),
            # el backend debe alojarlo en una celda de 8 bytes en el heap.
            if not postfix.children[1:] and symbol.type in SCALAR_TYPES:
                symbol.address_taken = True

            if hasattr(self, "register_borrow"):
                self.register_borrow(unary_ctx, symbol, is_mut, temporary=True)

        return RefT(inner_type, is_mut)

    def check_deref_operand(self, unary_ctx: RustiQParser.UnaryContext) -> Type | None:
        """Valida `*postfix`: requiere que el operando sea una referencia `&T` o `&mut T`."""
        postfix = unary_ctx.postfix()
        inner_type = self.visit(postfix)
        if inner_type is None:
            return None

        self.info.expr_type.put(postfix, inner_type)
        if not isinstance(inner_type, RefT):
            self.error(
                unary_ctx,
                E_BAD_OPERAND,
                f"No se puede desreferenciar un valor de tipo '{inner_type}'",
            )
            return None

        return inner_type.target