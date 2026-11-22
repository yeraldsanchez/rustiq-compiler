"""Préstamos: varios `&` o un solo `&mut` hasta el fin del ámbito.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas.
API pública que consulta `moves` (y a la inversa, `move_state`). Ninguno
modifica el estado del otro.

Vida de un préstamo:
- Nace temporal al evaluar `&x` o `&mut x` y muere al terminar la sentencia
  (o la condición de un `if`/`while`) que lo creó.
- Si un `let` guarda una referencia (`let r = &x;`), los préstamos creados por
  su inicializador quedan hasta que se cierra el ámbito donde vive `r`.
"""

from dataclasses import dataclass

from rustiq.errors import E_ASSIGN_WHILE_BORROWED


@dataclass
class _BorrowEntry:
    target_uid: int
    mutable: bool
    depth: int  # ámbitos abiertos al crearlo
    temporary: bool = True


class BorrowsMixin:
    def __init__(self) -> None:
        self._active_borrows: list[_BorrowEntry] = []

    # --- Consultas -------------------------------------------------------------

    def is_borrowed(self, symbol) -> bool:
        """True si el símbolo tiene un préstamo activo."""
        if symbol is None:
            return False
        return any(b.target_uid == symbol.uid for b in self._active_borrows)

    def is_mutably_borrowed(self, symbol) -> bool:
        if symbol is None:
            return False
        return any(b.target_uid == symbol.uid and b.mutable for b in self._active_borrows)

    # --- Altas -----------------------------------------------------------------

    def borrow_shared(self, symbol) -> None:
        self._add_borrow(symbol, mutable=False)

    def borrow_mutable(self, symbol) -> None:
        self._add_borrow(symbol, mutable=True)

    def _add_borrow(self, symbol, mutable: bool) -> None:
        depth = len(self._scopes_list())
        self._active_borrows.append(_BorrowEntry(symbol.uid, mutable, depth))

    # --- Vida ------------------------------------------------------------------

    def borrow_mark(self) -> int:
        """Marca el inicio de una sentencia; se pasa a `release_temporary_borrows`."""
        return len(self._active_borrows)

    def release_temporary_borrows(self, mark: int) -> None:
        """Suelta los préstamos temporales creados desde `mark`."""
        self._active_borrows = [
            b for i, b in enumerate(self._active_borrows) if i < mark or not b.temporary
        ]

    def keep_borrows(self, mark: int) -> None:
        """Los préstamos creados desde `mark` viven hasta el fin del ámbito actual."""
        depth = len(self._scopes_list())
        for b in self._active_borrows[mark:]:
            b.temporary = False
            b.depth = depth

    def release_scope_borrows(self) -> None:
        """Al cerrar un ámbito, suelta los préstamos que vivían en él."""
        depth = len(self._scopes_list())
        self._active_borrows = [b for b in self._active_borrows if b.depth < depth]

    # --- Reglas ----------------------------------------------------------------

    def visitAssignment(self, ctx):
        place = ctx.place()
        root_name = place.IDENT(0).getText()
        target = self.lookup(root_name)
        if self.is_borrowed(target):
            self.error(
                place,
                E_ASSIGN_WHILE_BORROWED,
                f"No se puede asignar a '{root_name}' mientras está prestado",
            )
        return super().visitAssignment(ctx)
