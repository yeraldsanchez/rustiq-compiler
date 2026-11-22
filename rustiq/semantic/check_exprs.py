"""Comprobación de tipos de expresiones y operadores (Carril B).

Los operadores binarios los escribió B en `b/etapa3-refs-borrows`; A los pasó
a main con su permiso.

Reglas de los operadores:
- `+ - * /` entre dos `i32` o dos `f64`; `%` solo entre `i32` (Wasm no tiene
  resto de f64).
- `== !=` entre dos valores iguales de tipo i32, f64, bool o char.
- `< <= > >=` entre dos i32, dos f64 o dos char.
- `&& ||` entre bool. El codegen hace cortocircuito.
- `-x` sobre i32 o f64, `!x` sobre bool, `*r` sobre una referencia.
"""

from antlr4.tree.Tree import TerminalNode

from rustiq.errors import E_BAD_OPERAND, E_BORROW_CONFLICT, E_BORROW_MUT_IMMUTABLE, E_TYPE_MISMATCH
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.types import BOOL, CHAR, F64, I32, STRING, RefT, Type, is_scalar

NUMERIC = (I32, F64)
EQUATABLE = (I32, F64, BOOL, CHAR)
ORDERED = (I32, F64, CHAR)


def operators(ctx) -> list[str]:
    """Los operadores entre los operandos de una regla binaria, en orden."""
    return [c.getText() for c in ctx.children if isinstance(c, TerminalNode)]


class ExprsMixin:
    def visitLiteral(self, ctx: P.LiteralContext):
        if ctx.STRING_LIT() is not None:
            return STRING
        if ctx.INT_LIT() is not None:
            return I32
        if ctx.FLOAT_LIT() is not None:
            return F64
        if ctx.CHAR_LIT() is not None:
            return CHAR
        return BOOL

    def visitUnary(self, ctx):
        inner = self.visit(ctx.postfix())
        if inner is not None:
            self.info.expr_type.put(ctx.postfix(), inner)
        if ctx.AMP() is not None:
            target_name = None
            primary = ctx.postfix().primary()
            if isinstance(primary, P.IdentPContext):
                target_name = primary.IDENT().getText()
            symbol = self.lookup(target_name) if target_name else None
            is_mut = ctx.MUT() is not None
            whole_variable = ctx.postfix().getChildCount() == 1  # `&x`, no `&x.campo`
            variable = symbol is not None and symbol.kind in ("local", "param")
            if variable and whole_variable and inner is not None and is_scalar(inner):
                symbol.address_taken = True  # el codegen lo guarda en una celda del heap
            if symbol is not None:
                if is_mut:
                    if not symbol.mutable:
                        self.error(ctx, E_BORROW_MUT_IMMUTABLE, f"'{symbol.name}' es inmutable y no puede recibir &mut")
                    elif self.is_borrowed(symbol):
                        self.error(ctx, E_BORROW_CONFLICT, f"'{symbol.name}' ya está prestado y no puede recibir &mut")
                    else:
                        self.borrow_mutable(symbol)
                else:
                    if self.is_mutably_borrowed(symbol):
                        self.error(ctx, E_BORROW_CONFLICT, f"'{symbol.name}' tiene préstamo mutable; no se puede crear &")
                    else:
                        self.borrow_shared(symbol)
            return RefT(inner, is_mut) if inner is not None else None
        if inner is None:
            return None
        if ctx.STAR() is not None:
            if not isinstance(inner, RefT):
                self.error(ctx, E_BAD_OPERAND, f"'*' necesita una referencia y se encontró {inner}")
                return None
            return inner.target
        if ctx.MINUS() is not None and inner not in NUMERIC:
            self.error(ctx, E_BAD_OPERAND, f"'-' necesita i32 o f64 y se encontró {inner}")
            return None
        if ctx.BANG() is not None and inner != BOOL:
            self.error(ctx, E_BAD_OPERAND, f"'!' necesita bool y se encontró {inner}")
            return None
        return inner

    def visitParenP(self, ctx: P.ParenPContext):
        return self.visit(ctx.expression())

    # --- Operadores binarios -----------------------------------------------------

    def visitMultiplicative(self, ctx: P.MultiplicativeContext):
        return self._binary_chain(ctx, ctx.unary())

    def visitAdditive(self, ctx: P.AdditiveContext):
        return self._binary_chain(ctx, ctx.multiplicative())

    def visitComparison(self, ctx: P.ComparisonContext):
        return self._binary_chain(ctx, ctx.additive())

    def visitLogicalAnd(self, ctx: P.LogicalAndContext):
        return self._binary_chain(ctx, ctx.comparison())

    def visitLogicalOr(self, ctx: P.LogicalOrContext):
        return self._binary_chain(ctx, ctx.logicalAnd())

    def _binary_chain(self, ctx, operands) -> Type | None:
        """Tipo de `a op b op c ...`, de izquierda a derecha. Anota cada operando."""
        types = [self.visit(operand) for operand in operands]
        for operand, t in zip(operands, types):
            if t is not None:
                self.info.expr_type.put(operand, t)
        if len(operands) == 1:
            return types[0]
        ops = operators(ctx.relOp()) if isinstance(ctx, P.ComparisonContext) else operators(ctx)
        current = types[0]
        for op, rhs, rhs_type in zip(ops, operands[1:], types[1:]):
            if current is None or rhs_type is None:
                return None
            current = self._binary_type(op, current, rhs, rhs_type)
        return current

    def _binary_type(self, op: str, left: Type, rhs, right: Type) -> Type | None:
        if op in ("&&", "||"):
            allowed, result = (BOOL,), BOOL
        elif op in ("==", "!="):
            allowed, result = EQUATABLE, BOOL
        elif op in ("<", "<=", ">", ">="):
            allowed, result = ORDERED, BOOL
        elif op == "%":
            allowed, result = (I32,), left
        else:
            allowed, result = NUMERIC, left
        if left not in allowed:
            self.error(rhs.parentCtx, E_BAD_OPERAND, f"'{op}' no se puede usar con {left}")
            return None
        if self.mismatch(rhs, E_TYPE_MISMATCH, left, right, f"El operando derecho de '{op}'"):
            return None
        return result
