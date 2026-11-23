"""Movimientos: estados de cada valor y uso después de mover.

API pública que consulta `borrows` (y a la inversa, `is_borrowed`). Ninguno
modifica el estado del otro.

Cada símbolo local o parámetro está disponible, movido o sin inicializar. Un
valor que no es Copy se mueve cuando una variable aparece sola en un lugar
que consume su valor: argumento, `return`, valor final de un bloque, dato de un
struct, tupla o enum, valor de un `match` o cuerpo de un brazo. Leer un campo
(`p.x`) no mueve.

Ramas: cada rama de un `if` o brazo de `match` empieza con el estado de
antes y, al terminar, cada variable queda en el peor estado entre el de antes y
el de cada rama. Así reponer una variable dentro de una rama no cuenta. Si las
ramas cubren todos los casos (`if` con `else`, `match`), el de antes no entra:
`let x: i32;` asignada en todas las ramas queda inicializada.

Ciclos: mover dentro de un ciclo una variable declarada fuera de él es error.

`visitIdentP` llama a `check_use`, y `visitLetDecl` a `consume` y
`track_symbol`.

Los operandos de una misma expresión (argumentos, campos, elementos) se mueven
uno por uno al visitarlos (`visit_and_consume`), así `f(s, s)` es error.
"""

from rustiq.errors import E_MOVE_OUT_OF_PLACE, E_MOVE_WHILE_BORROWED, E_UNINITIALIZED, E_USE_AFTER_MOVE
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.semantic.info import VARIABLE_KINDS
from rustiq.tree import unwrap
from rustiq.types import RefT, is_copy

# Estados de un símbolo
AVAILABLE = "available"
MOVED = "moved"
UNINITIALIZED = "uninitialized"

SEVERITY = {AVAILABLE: 0, UNINITIALIZED: 1, MOVED: 2}  # para unir ramas: gana el peor


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
        """Mueve la variable si `expression` es solo una variable cuyo tipo no es Copy.

        Mover un campo o un elemento que no es Copy (`p.nombre`, `a[0]`) mueve la
        variable entera: después no se puede usar ninguna parte de `p` ni de `a`.
        Así el valor movido y su dueño nunca comparten memoria. Mover desde una
        referencia (`*r`, `r.campo` con `r: &T`) es E_MOVE_OUT_OF_PLACE.
        """
        place = borrowed_place(expression)
        if place is not None:
            place_type = self.info.expr_type.get(place)
            if place_type is None or is_copy(place_type):
                return
            if isinstance(place, P.UnaryContext) or self._through_ref(place):
                self.error(
                    place, E_MOVE_OUT_OF_PLACE,
                    f"No se puede mover '{place.getText()}' ({place_type}) fuera de una referencia; "
                    "usa '&' para prestarlo",
                )
                return
            root = owned_root(place)
            root_symbol = self.info.symbol.get(root) if root is not None else None
            if root_symbol is not None:  # sin variable raíz es un temporal: nada que marcar
                self._move_symbol(root, root_symbol)
            return
        ident = moved_identifier(expression)
        symbol = self.info.symbol.get(ident) if ident is not None else None
        if symbol is None or symbol.type is None or is_copy(symbol.type):
            return
        self._move_symbol(ident, symbol)

    def _through_ref(self, place) -> bool:
        """True si algún tramo de `a.b[i]` pasa por una referencia (auto-deref)."""
        return any(isinstance(self.info.expr_type.get(s), RefT) for s in place.children[1:])

    def _move_symbol(self, ident, symbol) -> None:
        """Marca `symbol` como movido, salvo que esté prestado o fuera del ciclo."""
        if symbol.kind not in VARIABLE_KINDS:
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

    # --- Ramas ------------------------------------------------------------

    def branch_start(self) -> dict[int, str]:
        """Estado de antes de las ramas. Cada rama empieza desde aquí."""
        self.moved_in_branches.append(set())
        return dict(self.move_states)

    def branch_end(self, before: dict[int, str], branches: list[dict[int, str]], exhaustive: bool = False) -> None:
        """Une el estado de las ramas: cada variable queda en el peor estado.

        Si las ramas cubren todos los casos (`if` con `else`, `match`), el estado de
        antes no cuenta: una variable asignada en todas las ramas queda inicializada.
        """
        merged = {}
        for uid in set(before).union(*branches):
            states = [b.get(uid, AVAILABLE) for b in branches]
            if not exhaustive or not branches:
                states.append(before.get(uid, AVAILABLE))
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


def borrowed_place(node):
    """El nodo de `a.campo`, `a[i]` o `*r` si la expresión es solo eso, si no None.

    Una llamada (`f().campo` incluida) produce un temporal propio y no cuenta.
    """
    while node is not None:
        if isinstance(node, P.UnaryContext) and node.STAR() is not None:
            return node
        if isinstance(node, P.PostfixContext) and node.getChildCount() > 1:
            suffixes = node.children[1:]
            return None if any(isinstance(s, P.CallSuffixContext) for s in suffixes) else node
        node = unwrap(node)  # `-x`, `!x` y `&x` tienen dos hijos: aquí terminan en None
    return None


def owned_root(place):
    """El `IdentP` raíz de `a.b[i].c`, o None si la raíz no es una variable."""
    primary = place.primary()
    return primary if isinstance(primary, P.IdentPContext) else None


def moved_identifier(node):
    """El `IdentP` si la expresión es solo una variable (con o sin paréntesis), si no None."""
    while node is not None and not isinstance(node, P.IdentPContext):
        node = unwrap(node)
    return node
