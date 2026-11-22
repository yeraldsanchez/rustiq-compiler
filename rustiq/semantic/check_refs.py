"""Referencias y Strings.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas; si necesita
algo de otro mixin, llama su método público y nunca copia la lógica.
"""

from rustiq.errors import E_INVALID_REF, E_BORROW_CONFLICT, E_BORROW_MUT_IMMUTABLE
from rustiq.types import RefT, String
from rustiq.generated.RustiQParser import RustiQParser as P

class RefsMixin:
    # ------------------------------------------------------------------
    # visitRefP – maneja `&` o `&mut` frente a un identificador.
    # ------------------------------------------------------------------
    def visitRefP(self, ctx):
        """`refP` → '&' ('mut')? ident
        Registra el préstamo correspondiente en BorrowsMixin.
        """
        ident_ctx = ctx.ident()
        symbol = self.info.symbol.get(ident_ctx)

        if symbol is None:
            self.error(ctx, E_INVALID_REF, "referencia a símbolo inexistente")
            return

        # Detectar `&mut`
        if ctx.MUT():
            # Préstamo mutable: no debe haber ningún préstamo previo
            if self.is_borrowed(symbol):
                self.error(
                    ctx,
                    E_BORROW_MUT_IMMUTABLE,
                    f"'{symbol.name}' ya está prestado y no puede recibir &mut",
                )
                return
            self.borrow_mutable(symbol)
            mutable = True
        else:
            # Préstamo shared: conflicto si ya hay mutable
            if self.is_mutably_borrowed(symbol):
                self.error(
                    ctx,
                    E_BORROW_CONFLICT,
                    f"'{symbol.name}' tiene préstamo mutable; no se puede crear &",
                )
                return
            self.borrow_shared(symbol)
            mutable = False

        # Tipo resultante: referencia al tipo del símbolo
        self.info.expr_type[ctx] = RefT(symbol.type, mutable)

    # ------------------------------------------------------------------
    # visitStringLiteral – manejo de literales de String.
    # ------------------------------------------------------------------
    def visitStringLiteral(self, ctx):
        """Registra un literal String.
        El codegen emitirá `$str_new` para crear la cadena en memoria.
        """
        # El tipo es `String` (definido en rustiq/types.py)
        self.info.expr_type[ctx] = String
        # No hay préstamo aquí; simplemente se crea la constante.

    # ------------------------------------------------------------------
    # Liberación de préstamos al salir de bloques/funciones.
    # ------------------------------------------------------------------
    def exitBlock(self, ctx):
        """Al cerrar un bloque, liberar los préstamos locales creados dentro."""
        for uid, symbol in list(self.info.symbol.items()):
            if symbol.kind in ("local", "param"):
                self.release_borrow(symbol)

    def exitFunctionDecl(self, ctx):
        """Al terminar una función, liberar los préstamos de sus parámetros."""
        for uid, symbol in list(self.info.symbol.items()):
            if symbol.kind == "param":
                self.release_borrow(symbol)
