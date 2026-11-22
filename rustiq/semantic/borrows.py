"""Préstamos: varios `&` o un solo `&mut` hasta el fin del ámbito.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas.
API pública que consulta `moves` (y a la inversa, `move_state`). Ninguno
modifica el estado del otro.

Vida de un préstamo:
- Nace temporal al evaluar `&x` o `&mut x` y muere al terminar la sentencia
  (o la condición de un `if`/`while`) que lo creó.
- Si un `let` guarda una referencia (`let r = &x;`), los préstamos creados por
  su inicializador quedan hasta que se cierra el ámbito donde vive `r`.

Una función que devuelve `&T` no puede devolver una referencia a algo que
muere con ella (`E_RETURN_LOCAL_REF`): una variable o parámetro por valor, un
temporal (`&5`, `&f()`), o una variable-referencia que apunta a algo así.
Seguir una referencia recibida (`&p.x` con `p: &Punto`) sí vale. Se siguen también
llamadas que devuelven `&T` (sin anotaciones de vida, el resultado puede venir
de cualquier argumento), los brazos de un `match` y el valor final de un bloque.
"""

from dataclasses import dataclass

from antlr4 import ParserRuleContext

from rustiq.errors import E_ASSIGN_WHILE_BORROWED, E_DANGLING_REF, E_RETURN_LOCAL_REF
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.semantic.moves import moved_identifier
from rustiq.types import ArrayT, EnumT, RefT, StructT, TupleT


@dataclass
class _BorrowEntry:
    target_uid: int
    mutable: bool
    depth: int  # ámbitos abiertos al crearlo
    temporary: bool = True


class BorrowsMixin:
    def __init__(self) -> None:
        self._active_borrows: list[_BorrowEntry] = []
        self._local_refs: set[int] = set()  # uids de referencias a algo local

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

    def keep_borrows(self, mark: int, depth: int | None = None) -> None:
        """Los préstamos creados desde `mark` viven hasta el fin del ámbito `depth` (o el actual)."""
        depth = len(self._scopes_list()) if depth is None else depth
        for b in self._active_borrows[mark:]:
            b.temporary = False
            b.depth = depth

    def release_scope_borrows(self) -> None:
        """Al cerrar un ámbito, suelta los préstamos que vivían en él."""
        depth = len(self._scopes_list())
        self._active_borrows = [b for b in self._active_borrows if b.depth < depth]

    def may_hold_ref(self, t, seen=None) -> bool:
        """True si un valor de tipo `t` puede guardar una referencia."""
        seen = set() if seen is None else seen
        if isinstance(t, RefT):
            return True
        if isinstance(t, ArrayT):
            return self.may_hold_ref(t.elem, seen)
        if isinstance(t, TupleT):
            return any(self.may_hold_ref(e, seen) for e in t.elems)
        if isinstance(t, (StructT, EnumT)) and t.name not in seen:
            seen.add(t.name)
            if isinstance(t, StructT):
                fields = self.info.structs[t.name].fields.values()
            else:
                fields = [p for payload in self.info.enums[t.name].variants.values() for p in payload]
            return any(self.may_hold_ref(f, seen) for f in fields)
        return False

    # --- Referencias a locales -----------------------------------------------------

    def track_ref_origin(self, symbol, expression) -> None:
        """Recuerda si la referencia guardada en `symbol` apunta a algo local."""
        if self.points_to_local(expression):
            self._local_refs.add(symbol.uid)
        else:
            self._local_refs.discard(symbol.uid)

    def check_returned_ref(self, expression) -> None:
        """Reporta si una función que devuelve `&T` devuelve una referencia a un local."""
        if isinstance(self.fn_ret, RefT) and self.points_to_local(expression):
            self.error(expression, E_RETURN_LOCAL_REF, "No se puede devolver una referencia a un valor local")

    def points_to_local(self, expression) -> bool:
        ident = moved_identifier(expression)
        if ident is not None:  # `r`: depende de a qué apunta r
            symbol = self.info.symbol.get(ident)
            return symbol is not None and symbol.uid in self._local_refs
        operand = borrowed_operand(expression)
        if operand is None:
            return self._value_points_to_local(expression)
        primary = operand.primary()
        symbol = self.info.symbol.get(primary) if isinstance(primary, P.IdentPContext) else None
        if symbol is None:
            return True  # `&5`, `&f()`: un temporal
        if isinstance(symbol.type, RefT) and operand.getChildCount() > 1:
            return symbol.uid in self._local_refs  # `&r.x`: se sigue la referencia r
        return symbol.kind in ("local", "param")

    def _value_points_to_local(self, expression) -> bool:
        """Sigue llamadas, `match` y bloques: `id(&x)`, `match c { _ => &x }`, `{ &x }`."""
        call = _call_of(expression)
        if call is not None:
            callee, suffix = call
            sig = self.info.functions.get(callee.IDENT().getText())
            if sig is None or not isinstance(sig.ret, RefT) or suffix.argumentList() is None:
                return False
            # Sin anotaciones de vida, el resultado puede venir de cualquier argumento.
            return any(self.points_to_local(arg) for arg in suffix.argumentList().expression())
        primary = _bare_primary(expression)
        if isinstance(primary, P.MatchPContext):
            return any(self.points_to_local(arm.expression()) for arm in primary.matchExpr().matchArm())
        if isinstance(primary, P.BlockPContext):
            tail = primary.block().expression()
            return tail is not None and self.points_to_local(tail)
        return False

    # --- Reglas ----------------------------------------------------------------

    def scope_depth(self, symbol) -> int:
        """Cantidad de ámbitos abiertos hasta el que declaró `symbol` (incluido)."""
        for i, scope in enumerate(self._scopes_list()):
            if scope.get(symbol.name) is symbol:
                return i + 1
        return 0

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
        mark = self.borrow_mark()
        result = super().visitAssignment(ctx)
        whole = place.getChildCount() == 1 and ctx.assignOp().getText() == "="
        if target is not None and whole and isinstance(target.type, RefT):
            self._check_ref_outlives(target, ctx.expression())
            # `r = &x;`: el préstamo vive lo que vive `r`, no solo esta sentencia
            self.keep_borrows(mark, self.scope_depth(target))
        return result

    def _check_ref_outlives(self, ref_symbol, expression) -> None:
        """`r = &x` es error si `x` muere antes que `r` (se declaró en un bloque más interno)."""
        ref_depth = self.scope_depth(ref_symbol)
        for root in borrowed_roots(self, expression):
            symbol = self.info.symbol.get(root)
            if symbol is None or symbol.kind not in ("local", "param") or isinstance(symbol.type, RefT):
                continue
            if self.scope_depth(symbol) > ref_depth:
                self.error(
                    root, E_DANGLING_REF,
                    f"'{symbol.name}' no vive lo suficiente: muere al cerrar su bloque y "
                    f"'{ref_symbol.name}' lo seguiría usando",
                )


def borrowed_roots(analyzer, expression) -> list:
    """Los `IdentP` prestados por la expresión: `&x`, `&x.campo`, o los de los argumentos
    de una llamada que devuelve una referencia (`id(&x)`)."""
    operand = borrowed_operand(expression)
    if operand is not None:
        primary = operand.primary()
        return [primary] if isinstance(primary, P.IdentPContext) else []
    call = _call_of(expression)
    if call is None:
        return []
    callee, suffix = call
    sig = analyzer.info.functions.get(callee.IDENT().getText())
    if sig is None or not isinstance(sig.ret, RefT) or suffix.argumentList() is None:
        return []
    return [root for arg in suffix.argumentList().expression() for root in borrowed_roots(analyzer, arg)]


def _bare_primary(expression):
    """El `primary` si la expresión es solo eso (sin operadores ni sufijos), si no None."""
    node = expression
    while True:
        if isinstance(node, P.PostfixContext):
            return node.primary() if node.getChildCount() == 1 else None
        if isinstance(node, P.ParenPContext):
            node = node.expression()
        elif node.getChildCount() == 1 and isinstance(node.getChild(0), ParserRuleContext):
            node = node.getChild(0)
        else:
            return None


def _call_of(expression):
    """(callee, sufijo) si la expresión es solo `nombre(args)`, si no None."""
    node = expression
    while True:
        if isinstance(node, P.PostfixContext):
            suffixes = node.children[1:]
            primary = node.primary()
            if len(suffixes) == 1 and isinstance(suffixes[0], P.CallSuffixContext) and isinstance(primary, P.IdentPContext):
                return primary, suffixes[0]
            if suffixes:
                return None
            node = primary
        elif isinstance(node, P.ParenPContext):
            node = node.expression()
        elif isinstance(node, P.UnaryContext) and node.getChildCount() != 1:
            return None
        elif node.getChildCount() == 1 and isinstance(node.getChild(0), ParserRuleContext):
            node = node.getChild(0)
        else:
            return None


def borrowed_operand(expression):
    """El `postfix` de `&x...` si la expresión es solo eso (con o sin paréntesis), si no None."""
    node = expression
    while True:
        if isinstance(node, P.UnaryContext) and node.AMP() is not None:
            return node.postfix()
        if isinstance(node, P.ParenPContext):
            node = node.expression()
        elif node.getChildCount() == 1 and isinstance(node.getChild(0), ParserRuleContext):
            node = node.getChild(0)
        else:
            return None
