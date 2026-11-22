"""Tabla de símbolos, resolución de ámbitos y declaraciones locales (Carril B)."""

from rustiq.errors import E_BORROW_CONFLICT, E_REDECLARED, E_TYPE_MISMATCH, E_UNDECLARED
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.semantic.info import Symbol
from rustiq.types import RefT, Type, UNIT


def _is_borrow_operand(ident) -> bool:
    """True si el identificador es la raíz de lo que se presta: `&x`, `&mut x.campo`."""
    postfix = ident.parentCtx
    unary = postfix.parentCtx if isinstance(postfix, P.PostfixContext) else None
    return isinstance(unary, P.UnaryContext) and unary.AMP() is not None


class ScopesMixin:
    def _scopes_list(self) -> list[dict[str, Symbol]]:
        return self.__dict__.setdefault("_scopes", [])

    def push_scope(self) -> None:
        self._scopes_list().append({})

    def pop_scope(self) -> None:
        self.release_scope_borrows()
        self._scopes_list().pop()

    def _is_redeclared_in_current_or_params(self, name: str) -> bool:
        scopes = self._scopes_list()
        if not scopes:
            return False
        if name in scopes[-1]:
            return True
        # En visitFunctionDecl, scopes[-2] contiene exclusivamente los parámetros y scopes[-1] el bloque del cuerpo.
        # Si estamos en un bloque anidado más adentro, scopes[-2] ya no será exclusivo de parámetros.
        if len(scopes) >= 3:
            parent = scopes[-2]
            if name in parent and parent[name].kind == "param" and all(s.kind == "param" for s in parent.values()):
                return True
        return False

    def declare(self, name: str, type: Type, mutable: bool, kind: str, node) -> Symbol | None:
        scopes = self._scopes_list()
        if not scopes:
            self.push_scope()
        current = scopes[-1]

        # Regla G2: prohibido redeclarar en el mismo ámbito (incluyendo parámetros en el cuerpo);
        # permitido sombreado en bloques internos.
        if self._is_redeclared_in_current_or_params(name):
            self.error(node, E_REDECLARED, f"'{name}' ya fue declarado en este ámbito")
            return None

        uid = self.__dict__.get("_next_uid", 0)
        self._next_uid = uid + 1
        symbol = Symbol(uid=uid, name=name, type=type, mutable=mutable, kind=kind)
        current[name] = symbol
        return symbol

    def lookup(self, name: str) -> Symbol | None:
        for scope in reversed(self._scopes_list()):
            if name in scope:
                return scope[name]
        return None

    # ---------------------------------------------------------------
    # Visitors de declaraciones locales e identificadores (Carril B)
    # ---------------------------------------------------------------

    def visitLetDecl(self, ctx):
        name = ctx.IDENT().getText()
        mutable = ctx.MUT() is not None

        has_type_ann = ctx.type_() is not None
        has_init = ctx.expression() is not None

        declared_type: Type | None = self.resolve_type(ctx.type_()) if has_type_ann else None
        mark = self.borrow_mark()
        init_type: Type | None = self.visit(ctx.expression()) if has_init else None

        final_type: Type | None = declared_type if has_type_ann else init_type
        if has_type_ann and has_init:
            self.mismatch(
                ctx.expression(),
                E_TYPE_MISMATCH,
                declared_type,
                init_type,
                f"Inicializador de '{name}'",
            )
        elif not has_type_ann and not has_init:
            # T4: sin anotación ni inicializador no hay de dónde inferir el tipo
            self.error(
                ctx,
                E_TYPE_MISMATCH,
                f"No se puede inferir el tipo de '{name}' sin anotación ni inicializador",
            )
        elif not has_type_ann and init_type == UNIT:
            self.error(ctx, E_TYPE_MISMATCH, f"No se puede inferir el tipo de '{name}' desde '()'")
            final_type = None

        # Se declara aunque el tipo sea None (error previo): así los usos
        # siguientes no reportan E_UNDECLARED en cascada y `mismatch` calla.
        symbol = self.declare(name, final_type, mutable, "local", ctx.IDENT())
        if symbol is None:
            return None
        self.info.symbol.put(ctx, symbol)
        if isinstance(final_type, RefT):
            self.keep_borrows(mark)  # `let r = &x;`: el préstamo vive lo que vive `r`
            if has_init:
                self.track_ref_origin(symbol, ctx.expression())
        if has_init:
            self.consume(ctx.expression())
        # Con tipo None ya hubo un error: no se reporta además "sin inicializar"
        self.track_symbol(symbol, initialized=has_init or final_type is None)
        return None

    def visitIdentP(self, ctx):
        name = ctx.IDENT().getText()
        symbol = self.lookup(name)
        if symbol is None:
            self.error(ctx.IDENT(), E_UNDECLARED, f"Identificador '{name}' no declarado")
            return None

        self.info.symbol.put(ctx, symbol)
        if self.check_use(symbol, ctx) and not _is_borrow_operand(ctx) and self.is_mutably_borrowed(symbol):
            # Mientras vive un `&mut`, el dueño no se puede leer (`&x` lo revisa visitUnary).
            self.error(
                ctx, E_BORROW_CONFLICT,
                f"'{name}' tiene un préstamo mutable activo y no se puede usar hasta que termine",
            )
        return symbol.type
