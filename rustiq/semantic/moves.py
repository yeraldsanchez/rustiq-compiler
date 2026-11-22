"""Movimientos: estados de cada valor y uso después de mover.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas.

API pública que consulta `borrows` (y a la inversa, `is_borrowed`). Ninguno
modifica el estado del otro.

Cada símbolo local o parámetro está disponible, movido o sin inicializar. Un
valor que no es Copy (G1) se mueve cuando una variable aparece sola en un lugar
que consume su valor: argumento, `return`, valor final de un bloque, dato de un
struct, tupla o enum, valor de un `match` o cuerpo de un brazo. Leer un campo
(`p.x`) no mueve.

Ramas (G8): cada rama de un `if` o brazo de `match` empieza con el estado de
antes y, al terminar, cada variable queda en el peor estado entre el de antes y
el de cada rama. Así reponer una variable dentro de una rama no cuenta.

Ciclos (G8): mover dentro de un ciclo una variable declarada fuera de él es error.

Ya conectado desde B: `visitIdentP` llama a `check_use` y `visitLetDecl` a
`consume` y `track_symbol`.

Los operandos de una misma expresión (argumentos, campos, elementos) se mueven
uno por uno al visitarlos (`visit_and_consume`), así `f(s, s)` es error.
"""

from antlr4 import ParserRuleContext

from rustiq.errors import E_MOVE_WHILE_BORROWED, E_UNINITIALIZED, E_USE_AFTER_MOVE
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.types import is_copy

# Estados de un símbolo
AVAILABLE = "available"
MOVED = "moved"
UNINITIALIZED = "uninitialized"

SEVERITY = {AVAILABLE: 0, UNINITIALIZED: 1, MOVED: 2}  # para unir ramas: gana el peor
MOVABLE_KINDS = ("local", "param")


class MovesMixin:
    def move_state(self, symbol) -> str:
        """Estado actual del símbolo: AVAILABLE, MOVED o UNINITIALIZED."""
        return self.move_states.get(symbol.uid, AVAILABLE)

    def track_symbol(self, symbol, initialized: bool = True) -> None:
        """Registra una variable recién declarada y el ciclo en que vive."""
        self.move_loop_depth[symbol.uid] = self.loop_depth
        self.move_states[symbol.uid] = AVAILABLE if initialized else UNINITIALIZED

    def mark_initialized(self, symbol) -> None:
        self.move_states[symbol.uid] = AVAILABLE

    def check_use(self, symbol, node) -> bool:
        """Reporta si se lee una variable movida o sin inicializar. True si se puede usar."""
        state = self.move_state(symbol)
        if state == MOVED:
            self.error(node, E_USE_AFTER_MOVE, f"'{symbol.name}' se usó después de moverse")
        elif state == UNINITIALIZED:
            self.error(node, E_UNINITIALIZED, f"'{symbol.name}' se usó antes de asignarle un valor")
        return state == AVAILABLE

    def consume(self, expression) -> None:
        """Mueve la variable si `expression` es solo una variable cuyo tipo no es Copy."""
        ident = moved_identifier(expression)
        symbol = self.info.symbol.get(ident) if ident is not None else None
        if symbol is None or symbol.kind not in MOVABLE_KINDS or symbol.type is None or is_copy(symbol.type):
            return
        if self.move_state(symbol) != AVAILABLE:
            return  # check_use ya reportó el error
        # Si el símbolo está prestado, no se permite moverlo.
        if self.is_borrowed(symbol):
            self.error(
                ident,
                E_MOVE_WHILE_BORROWED,
                f"'{symbol.name}' no se puede mover mientras está prestado",
            )
            return
        declared_in = self.move_loop_depth.get(symbol.uid)
        if declared_in is not None and declared_in < self.loop_depth:
            self.error(
                ident, E_USE_AFTER_MOVE,
                f"'{symbol.name}' se declaró fuera del ciclo y se movería en cada vuelta",
            )
            return
        self.move_states[symbol.uid] = MOVED
        if self.moved_in_branches:
            self.moved_in_branches[-1].add(symbol.uid)

    def visit_and_consume(self, expressions, moves: bool = True) -> list:
        """Visita cada expresión y la mueve enseguida, antes de la siguiente.

        Así `f(s, s)` o `(s, s)` reportan uso después de mover en el segundo `s`.
        Con `moves=False` solo se visitan (los `print_*` del host no se quedan
        con el valor).
        """
        types = []
        for expression in expressions:
            types.append(self.visit(expression))
            if moves:
                self.consume(expression)
        return types

    # --- Ramas (G8) ------------------------------------------------------------

    def branch_start(self) -> dict[int, str]:
        """Estado de antes de las ramas. Cada rama empieza desde aquí."""
        self.moved_in_branches.append(set())
        return dict(self.move_states)

    def branch_end(self, before: dict[int, str], branches: list[dict[int, str]]) -> None:
        """Une el estado de las ramas: cada variable queda en el peor estado."""
        merged = {}
        for uid in set(before).union(*branches):
            states = [before.get(uid, AVAILABLE)] + [b.get(uid, AVAILABLE) for b in branches]
            merged[uid] = max(states, key=SEVERITY.__getitem__)
        moved = self.moved_in_branches.pop()
        for uid in moved:
            merged[uid] = MOVED  # movida en alguna rama, aunque se haya repuesto ahí
        if self.moved_in_branches:
            self.moved_in_branches[-1].update(moved)
        self.move_states = merged

    def branch_restore(self, before: dict[int, str]) -> None:
        """Vuelve al estado de antes para empezar la siguiente rama."""
        self.move_states = dict(before)


def moved_identifier(node):
    """El `IdentP` si la expresión es solo una variable (con o sin paréntesis), si no None."""
    while not isinstance(node, P.IdentPContext):
        if isinstance(node, P.ParenPContext):
            node = node.expression()
        elif node.getChildCount() == 1 and isinstance(node.getChild(0), ParserRuleContext):
            node = node.getChild(0)
        else:
            return None
    return node
