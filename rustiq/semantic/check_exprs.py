"""Comprobación de tipos de literales, operadores y asignaciones (Carril B)."""

from rustiq.errors import (
    E_ASSIGN_IMMUTABLE,
    E_BAD_OPERAND,
    E_TYPE_MISMATCH,
    E_UNDECLARED,
    E_UNKNOWN_FIELD,
)
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.types import BOOL, CHAR, F64, I32, STRING, ArrayT, RefT, StructT, Type


class ExprsMixin:
    def visitLiteral(self, ctx: RustiQParser.LiteralContext) -> Type:
        if ctx.INT_LIT() is not None:
            return I32
        if ctx.FLOAT_LIT() is not None:
            return F64
        if ctx.CHAR_LIT() is not None:
            return CHAR
        if ctx.STRING_LIT() is not None:
            return STRING
        return BOOL

    def visitParenP(self, ctx: RustiQParser.ParenPContext) -> Type | None:
        return self.visit(ctx.expression())

    def visitUnary(self, ctx: RustiQParser.UnaryContext) -> Type | None:
        if ctx.AMP() is not None:
            return self.check_borrow_operand(ctx)
        if ctx.STAR() is not None:
            return self.check_deref_operand(ctx)

        inner = self.visit(ctx.postfix())
        if inner is None:
            return None
        self.info.expr_type.put(ctx.postfix(), inner)

        if ctx.MINUS() is not None:
            if inner not in (I32, F64):
                self.error(ctx, E_BAD_OPERAND, f"El operador unario '-' no aplica al tipo '{inner}'")
                return None
            return inner

        if ctx.BANG() is not None:
            if inner != BOOL:
                self.error(ctx, E_BAD_OPERAND, f"El operador '!' requiere 'bool', se encontró '{inner}'")
                return None
            return BOOL

        return inner

    def _check_binary_chain(self, operands, operators: list[str]) -> Type | None:
        types = [self.visit(op) for op in operands]
        for operand, t in zip(operands, types):
            if t is not None:
                self.info.expr_type.put(operand, t)

        current = types[0]
        for op, rhs_node, rhs_type in zip(operators, operands[1:], types[1:]):
            if current is None or rhs_type is None:
                return None
            if op in ("&&", "||"):
                if current != BOOL or rhs_type != BOOL:
                    self.error(rhs_node, E_BAD_OPERAND, f"El operador '{op}' requiere operandos 'bool'")
                    return None
                current = BOOL
            elif op in ("==", "!="):
                if current != rhs_type:
                    self.mismatch(rhs_node, E_TYPE_MISMATCH, current, rhs_type, f"Comparación '{op}'")
                    return None
                if current not in (I32, F64, BOOL, CHAR):
                    self.error(rhs_node, E_BAD_OPERAND, f"No se puede comparar valores de tipo '{current}' con '{op}'")
                    return None
                current = BOOL
            elif op in ("<", "<=", ">", ">="):
                if current != rhs_type or current not in (I32, F64, CHAR):
                    self.error(rhs_node, E_BAD_OPERAND, f"El operador '{op}' requiere dos operandos del mismo tipo")
                    return None
                current = BOOL
            else:
                if current not in (I32, F64) or rhs_type != current:
                    self.error(rhs_node, E_BAD_OPERAND, f"Operador '{op}' inválido entre '{current}' y '{rhs_type}'")
                    return None
        return current

    def visitMultiplicative(self, ctx: RustiQParser.MultiplicativeContext) -> Type | None:
        ops = [ctx.getChild(i).getText() for i in range(1, ctx.getChildCount(), 2)]
        return self._check_binary_chain(ctx.unary(), ops)

    def visitAdditive(self, ctx: RustiQParser.AdditiveContext) -> Type | None:
        ops = [ctx.getChild(i).getText() for i in range(1, ctx.getChildCount(), 2)]
        return self._check_binary_chain(ctx.multiplicative(), ops)

    def visitComparison(self, ctx: RustiQParser.ComparisonContext) -> Type | None:
        operands = ctx.additive()
        if ctx.relOp() is None:
            return self.visit(operands[0])
        return self._check_binary_chain(operands, [ctx.relOp().getText()])

    def visitLogicalAnd(self, ctx: RustiQParser.LogicalAndContext) -> Type | None:
        operands = ctx.comparison()
        if len(operands) == 1:
            return self.visit(operands[0])
        return self._check_binary_chain(operands, ["&&"] * (len(operands) - 1))

    def visitLogicalOr(self, ctx: RustiQParser.LogicalOrContext) -> Type | None:
        operands = ctx.logicalAnd()
        if len(operands) == 1:
            return self.visit(operands[0])
        return self._check_binary_chain(operands, ["||"] * (len(operands) - 1))

    def visitAssignment(self, ctx: RustiQParser.AssignmentContext):
        place = ctx.place()
        root_name = place.IDENT(0).getText()
        symbol = self.lookup(root_name)
        if symbol is None:
            self.error(place.IDENT(0), E_UNDECLARED, f"Identificador '{root_name}' no declarado")
            self.visit(ctx.expression())
            return None

        self.info.symbol.put(ctx, symbol)
        place_type = self._resolve_place_type(place, symbol)
        rhs_type = self.visit(ctx.expression())

        if place_type is not None and rhs_type is not None:
            op = ctx.assignOp().getText()
            if op == "=":
                self.mismatch(ctx.expression(), E_TYPE_MISMATCH, place_type, rhs_type, f"Asignación a '{root_name}'")
            else:
                if place_type not in (I32, F64) or rhs_type != place_type:
                    self.error(ctx.expression(), E_BAD_OPERAND, f"Operador '{op}' inválido entre '{place_type}' y '{rhs_type}'")
        return None

    def _resolve_place_type(self, place: RustiQParser.PlaceContext, symbol) -> Type | None:
        current_type = symbol.type
        through_mut_ref = False
        if isinstance(current_type, RefT):
            through_mut_ref = current_type.mutable
            current_type = current_type.target

        has_accessors = place.getChildCount() > 1
        if not has_accessors:
            if not symbol.mutable:
                self.error(place, E_ASSIGN_IMMUTABLE, f"No se puede asignar a la variable inmutable '{symbol.name}'")
            return current_type

        if not symbol.mutable and not through_mut_ref:
            self.error(place, E_ASSIGN_IMMUTABLE, f"No se puede modificar un campo o elemento de '{symbol.name}' porque es inmutable")

        i = 1
        while i < place.getChildCount():
            token_text = place.getChild(i).getText()
            if token_text == ".":
                field_node = place.getChild(i + 1)
                field_name = field_node.getText()
                if isinstance(current_type, RefT):
                    if not current_type.mutable:
                        self.error(place, E_ASSIGN_IMMUTABLE, f"No se puede mutar a través de '{current_type}'")
                    current_type = current_type.target
                if not isinstance(current_type, StructT):
                    self.error(field_node, E_BAD_OPERAND, f"El tipo {current_type} no tiene campos")
                    return None
                fields = self.info.structs[current_type.name].fields
                if field_name not in fields:
                    self.error(field_node, E_UNKNOWN_FIELD, f"'{current_type.name}' no tiene el campo '{field_name}'")
                    return None
                current_type = fields[field_name]
                i += 2
            elif token_text == "[":
                idx_expr = place.getChild(i + 1)
                idx_type = self.visit(idx_expr)
                if idx_type is not None:
                    self.mismatch(idx_expr, E_TYPE_MISMATCH, I32, idx_type, "Índice de arreglo")
                if isinstance(current_type, RefT):
                    if not current_type.mutable:
                        self.error(place, E_ASSIGN_IMMUTABLE, f"No se puede mutar a través de '{current_type}'")
                    current_type = current_type.target
                if isinstance(current_type, ArrayT):
                    current_type = current_type.elem
                else:
                    self.error(place, E_BAD_OPERAND, f"El tipo '{current_type}' no es indexable")
                    return None
                i += 3
            else:
                i += 1
        return current_type
