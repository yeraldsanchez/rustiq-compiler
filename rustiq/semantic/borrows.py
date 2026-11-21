"""Préstamos: varios `&` o un solo `&mut` hasta el fin del ámbito (Carril B)."""

from dataclasses import dataclass

from rustiq.errors import (
    E_ASSIGN_WHILE_BORROWED,
    E_BORROW_CONFLICT,
    E_BORROW_MUT_IMMUTABLE,
    E_RETURN_LOCAL_REF,
)
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.info import Symbol
from rustiq.types import RefT


@dataclass
class _BorrowEntry:
    target_uid: int
    mutable: bool
    scope_depth: int
    temporary: bool = False
    holder_uid: int | None = None


class BorrowsMixin:
    def _borrows_list(self) -> list[_BorrowEntry]:
        return self.__dict__.setdefault("_active_borrows", [])

    def _borrow_origins(self) -> dict[int, int]:
        return self.__dict__.setdefault("_borrow_origins_map", {})

    def _current_scope_depth(self) -> int:
        return len(self.__dict__.get("_scopes", []))

    def is_borrowed(self, symbol: Symbol) -> bool:
        """True si el símbolo tiene al menos un préstamo activo (& o &mut)."""
        if symbol is None:
            return False
        return any(b.target_uid == symbol.uid for b in self._borrows_list())

    def pop_scope(self) -> None:
        depth = self._current_scope_depth()
        self._active_borrows = [b for b in self._borrows_list() if b.scope_depth < depth]
        super().pop_scope()

    def _clear_temporary_borrows(self) -> None:
        self._active_borrows = [b for b in self._borrows_list() if not b.temporary]

    def register_borrow(
        self,
        node,
        target: Symbol,
        mutable: bool,
        *,
        temporary: bool = True,
        holder_uid: int | None = None,
    ) -> bool:
        if mutable and not target.mutable:
            self.error(
                node,
                E_BORROW_MUT_IMMUTABLE,
                f"No se puede prestar como mutable '&mut' la variable inmutable '{target.name}'",
            )
            return False

        existing = [b for b in self._borrows_list() if b.target_uid == target.uid]
        if mutable and existing:
            self.error(
                node,
                E_BORROW_CONFLICT,
                f"No se puede prestar '{target.name}' como '&mut' porque ya tiene un préstamo activo",
            )
            return False
        if not mutable and any(b.mutable for b in existing):
            self.error(
                node,
                E_BORROW_CONFLICT,
                f"No se puede prestar '{target.name}' como '&' mientras existe un préstamo '&mut' activo",
            )
            return False

        self._borrows_list().append(
            _BorrowEntry(
                target_uid=target.uid,
                mutable=mutable,
                scope_depth=self._current_scope_depth(),
                temporary=temporary,
                holder_uid=holder_uid,
            )
        )
        return True

    @staticmethod
    def _extract_root_ident(expr_ctx) -> str | None:
        node = expr_ctx
        while node is not None:
            if isinstance(node, RustiQParser.IdentPContext):
                return node.IDENT().getText()
            if isinstance(node, RustiQParser.ParenPContext):
                node = node.expression()
                continue
            if hasattr(node, "getChildCount") and node.getChildCount() == 1:
                node = node.getChild(0)
                continue
            break
        return None

    @staticmethod
    def _extract_borrow_expr(expr_ctx):
        node = expr_ctx
        while node is not None:
            if isinstance(node, RustiQParser.UnaryContext) and node.AMP() is not None:
                return (node.MUT() is not None), node.postfix()
            if isinstance(node, RustiQParser.ParenPContext):
                node = node.expression()
                continue
            if hasattr(node, "getChildCount") and node.getChildCount() == 1:
                node = node.getChild(0)
                continue
            break
        return None

    def visitLetDecl(self, ctx: RustiQParser.LetDeclContext):
        super().visitLetDecl(ctx)
        symbol = self.info.symbol.get(ctx)
        if symbol is None or ctx.expression() is None:
            self._clear_temporary_borrows()
            return None

        borrow_info = self._extract_borrow_expr(ctx.expression())
        if borrow_info is not None:
            _, postfix = borrow_info
            target_name = self._extract_root_ident(postfix)
            target_sym = self.lookup(target_name) if target_name else None
            if target_sym is not None:
                for b in reversed(self._borrows_list()):
                    if b.target_uid == target_sym.uid and b.temporary:
                        b.temporary = False
                        b.holder_uid = symbol.uid
                        break
                if target_sym.kind in ("local", "param"):
                    self._borrow_origins()[symbol.uid] = target_sym.uid
        else:
            src_name = self._extract_root_ident(ctx.expression())
            src_sym = self.lookup(src_name) if src_name else None
            if src_sym is not None and src_sym.uid in self._borrow_origins():
                self._borrow_origins()[symbol.uid] = self._borrow_origins()[src_sym.uid]

        self._clear_temporary_borrows()
        return None

    def visitAssignStmt(self, ctx: RustiQParser.AssignStmtContext):
        res = super().visitAssignStmt(ctx)
        self._clear_temporary_borrows()
        return res

    def visitExprStmt(self, ctx: RustiQParser.ExprStmtContext):
        res = super().visitExprStmt(ctx)
        self._clear_temporary_borrows()
        return res

    def visitAssignment(self, ctx: RustiQParser.AssignmentContext):
        place = ctx.place()
        root_name = place.IDENT(0).getText()
        target = self.lookup(root_name)
        if target is not None and self.is_borrowed(target):
            self.error(
                place,
                E_ASSIGN_WHILE_BORROWED,
                f"No se puede asignar a '{root_name}' mientras tiene un préstamo activo",
            )
        return super().visitAssignment(ctx)

    def visitReturnStmt(self, ctx: RustiQParser.ReturnStmtContext):
        res = super().visitReturnStmt(ctx)
        expr = ctx.expression()
        if expr is not None:
            self._check_return_not_local_ref(expr)
        self._clear_temporary_borrows()
        return res

    def _check_return_not_local_ref(self, expr_ctx) -> None:
        borrow_info = self._extract_borrow_expr(expr_ctx)
        if borrow_info is not None:
            _, postfix = borrow_info
            target_name = self._extract_root_ident(postfix)
            target_sym = self.lookup(target_name) if target_name else None
            if target_sym is not None and target_sym.kind in ("local", "param"):
                self.error(
                    expr_ctx,
                    E_RETURN_LOCAL_REF,
                    f"No se puede retornar una referencia a la variable local '{target_sym.name}'",
                )
            return

        ident_name = self._extract_root_ident(expr_ctx)
        if ident_name is not None:
            sym = self.lookup(ident_name)
            if sym is not None and isinstance(sym.type, RefT) and sym.uid in self._borrow_origins():
                self.error(
                    expr_ctx,
                    E_RETURN_LOCAL_REF,
                    f"No se puede retornar una referencia a una variable local mediante '{sym.name}'",
                )
