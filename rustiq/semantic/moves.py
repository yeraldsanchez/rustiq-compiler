"""Movimientos: estados de cada valor y uso después de mover.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas.

API pública que consulta `borrows` (y a la inversa, `is_borrowed`). Ninguno
modifica el estado del otro.
"""

# Estados de un símbolo
AVAILABLE = "available"
MOVED = "moved"
UNINITIALIZED = "uninitialized"


class MovesMixin:
    def move_state(self, symbol) -> str:
        """Estado actual del símbolo: AVAILABLE, MOVED o UNINITIALIZED."""
        raise NotImplementedError
