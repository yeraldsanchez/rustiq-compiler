"""Préstamos: varios `&` o un solo `&mut` hasta el fin del ámbito.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas.

API pública que consulta `moves` (y a la inversa, `move_state`). Ninguno
modifica el estado del otro.
"""


class BorrowsMixin:
    def is_borrowed(self, symbol) -> bool:
        """True si el símbolo tiene un préstamo activo."""
        raise NotImplementedError
