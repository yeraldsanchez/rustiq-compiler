"""Préstamos: varios `&` o un solo `&mut` hasta el fin del ámbito.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas.
API pública que consulta `moves` (y a la inversa, `move_state`). Ninguno
modifica el estado del otro.
"""

from dataclasses import dataclass
from rustiq.errors import E_BORROWED_MUTABLE, E_BORROWED_SHARED, E_MOVE_WHILE_BORROWED
from rustiq.types import is_mutable_ref, is_shared_ref

@dataclass
class _BorrowEntry:
    target_uid: int
    mutable: bool
    temporary: bool = True

class BorrowsMixin:
    def __init__(self):
        self._active_borrows: list[_BorrowEntry] = []

    def is_borrowed(self, symbol) -> bool:
        if symbol is None:
            return False
        return any(b.target_uid == symbol.uid for b in self._active_borrows)

    def is_mutably_borrowed(self, symbol) -> bool:
        if symbol is None:
            return False
        return any(b.target_uid == symbol.uid and b.mutable for b in self._active_borrows)

    def borrow_shared(self, symbol, temporary: bool = True) -> None:
        self._active_borrows.append(_BorrowEntry(target_uid=symbol.uid, mutable=False, temporary=temporary))

    def borrow_mutable(self, symbol, temporary: bool = True) -> None:
        self._active_borrows.append(_BorrowEntry(target_uid=symbol.uid, mutable=True, temporary=temporary))

    def clear_temporary_borrows(self) -> None:
        self._active_borrows = [b for b in self._active_borrows if not b.temporary]

    def visitLetDecl(self, ctx):
        res = super().visitLetDecl(ctx)
        if ctx.expression() is not None:
            for b in self._active_borrows:
                b.temporary = False
        return res

    def visitAssignment(self, ctx):
        place = ctx.place()
        root_name = place.IDENT(0).getText()
        target = self.lookup(root_name)
        if target is not None and self.is_borrowed(target):
            self.error(
                place,
                E_MOVE_WHILE_BORROWED,
                f"'{root_name}' no se puede mover mientras está prestado",
            )
        return super().visitAssignment(ctx)
