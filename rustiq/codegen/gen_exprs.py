"""Generación de código de literales, operadores y variables.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos. `visitLiteral` y `visitAssignment` los
implementó A con su permiso para cerrar movimientos. Los operadores son los de
B en `b/etapa3-refs-borrows`, pasados por A, con cortocircuito en `&&` y `||`.
"""

from rustiq.codegen.gen_arrays import array_of
from rustiq.codegen.gen_structs import SLOT_SIZE, slot_offset
from rustiq.codegen.wasm_types import wasm_type
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.check_exprs import operators
from rustiq.tree import place_accessors
from rustiq.types import F64, StructT, Type, is_scalar

# Instrucción de cada operador binario según el tipo de los operandos.
BINARY_I32 = {
    "+": "add", "-": "sub", "*": "mul", "/": "div_s", "%": "rem_s",
    "==": "eq", "!=": "ne", "<": "lt_s", "<=": "le_s", ">": "gt_s", ">=": "ge_s",
}
BINARY_F64 = {
    "+": "add", "-": "sub", "*": "mul", "/": "div",
    "==": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge",
}

# Sufijos que nombran una ranura: se puede tomar su dirección.
ACCESSORS = (RustiQParser.FieldSuffixContext, RustiQParser.IndexSuffixContext)


# Escapes de un literal de char (fragmento ESC de la gramática).
CHAR_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}

# Instrucción de cada asignación compuesta según el tipo.
COMPOUND_I32 = {"+=": "add", "-=": "sub", "*=": "mul", "/=": "div_s"}
COMPOUND_F64 = {"+=": "add", "-=": "sub", "*=": "mul", "/=": "div"}


def char_value(raw_literal: str) -> int:
    inner = raw_literal[1:-1]
    return ord(CHAR_ESCAPES[inner[1]] if inner.startswith("\\") else inner)


class ExprsGenMixin:
    def visitLiteral(self, ctx: RustiQParser.LiteralContext):
        text = ctx.getText()
        if ctx.INT_LIT() is not None:
            self.emit(f"i32.const {text}")
        elif ctx.FLOAT_LIT() is not None:
            self.emit(f"f64.const {text}")
        elif ctx.CHAR_LIT() is not None:
            self.emit(f"i32.const {char_value(text)}")
        elif ctx.STRING_LIT() is not None:
            self.emit_string_literal(text)
        else:
            self.emit(f"i32.const {1 if ctx.TRUE() is not None else 0}")

    def visitLetDecl(self, ctx: RustiQParser.LetDeclContext):
        symbol = self.info.symbol.get(ctx)
        if symbol is not None:
            self.declare_symbol(symbol)
            if ctx.expression() is not None:
                self.store_symbol(symbol, lambda: self.visit(ctx.expression()))

    def visitIdentP(self, ctx: RustiQParser.IdentPContext):
        symbol = self.info.symbol.get(ctx)
        if symbol is not None:
            self.load_symbol(symbol)

    def visitParenP(self, ctx: RustiQParser.ParenPContext):
        self.visit(ctx.expression())

    # --- Operadores ------------------------------------------------------------

    def visitUnary(self, ctx: RustiQParser.UnaryContext):
        operand = ctx.postfix()
        if ctx.MINUS() is not None:
            if self.info.expr_type.get(operand) == F64:
                self.visit(operand)
                self.emit("f64.neg")
            else:
                self.emit("i32.const 0")
                self.visit(operand)
                self.emit("i32.sub")
        elif ctx.BANG() is not None:
            self.visit(operand)
            self.emit("i32.eqz")
        elif ctx.AMP() is not None or ctx.STAR() is not None:
            self._ref_or_deref(ctx, operand)
        else:
            self.visit(operand)

    def _ref_or_deref(self, ctx, operand) -> None:
        if ctx.STAR() is not None:
            self.visit(operand)
            target = self.info.expr_type.get(operand).target
            if is_scalar(target):  # una referencia a escalar apunta a su celda
                self.emit(f"{wasm_type(target)}.load")
            return  # a un struct, tupla o array: es el mismo puntero
        if not is_scalar(self.info.expr_type.get(operand)):
            self.visit(operand)  # `&p` de un struct, tupla o array: el mismo puntero
        elif self._boxed_variable(operand) is not None:
            self.emit(f"local.get {self.cell_name(self._boxed_variable(operand))}")
        elif isinstance(operand.children[-1], ACCESSORS):
            self._emit_postfix_address(operand)
        else:
            self._emit_temporary_cell(operand)

    def _boxed_variable(self, postfix):
        """El símbolo si `postfix` es solo una variable guardada en celda; si no None."""
        primary = postfix.primary()
        if postfix.getChildCount() != 1 or not isinstance(primary, RustiQParser.IdentPContext):
            return None
        symbol = self.info.symbol.get(primary)
        return symbol if symbol is not None and symbol.address_taken else None

    def _emit_postfix_address(self, postfix) -> None:
        """`&p.x` o `&a[i]`: la dirección de la ranura, no una copia del valor."""
        *leading, last = postfix.children[1:]
        self.emit_postfix(postfix.primary(), leading)
        owner = self.info.expr_type.get(last)
        if isinstance(last, RustiQParser.FieldSuffixContext):
            self.emit_slot_address(owner, field=last.IDENT().getText())
        else:
            self.emit_slot_address(owner, index=last.expression())

    def _emit_temporary_cell(self, operand) -> None:
        """`&5` o `&f()`: guarda el valor en una celda nueva y deja su dirección."""
        cell = self.new_temp(StructT("_"))
        self.emit(f"i32.const {SLOT_SIZE}")
        self.emit("call $alloc")
        self.emit(f"local.tee {cell}")
        self.visit(operand)
        self.emit(f"{wasm_type(self.info.expr_type.get(operand))}.store")
        self.emit(f"local.get {cell}")

    def emit_slot_address(self, owner: Type, field: str | None = None, index=None) -> Type:
        """Con el puntero de `owner` en la pila, deja la dirección de su campo o elemento."""
        if field is not None:
            slot, field_type = self.field_slot(owner, field)
            self.emit(f"i32.const {slot_offset(slot)}")
            self.emit("i32.add")
            return field_type
        array = array_of(owner)
        self.emit_element_address(index, array.size)
        return array.elem

    def visitMultiplicative(self, ctx: RustiQParser.MultiplicativeContext):
        self._arithmetic_chain(ctx.unary(), operators(ctx))

    def visitAdditive(self, ctx: RustiQParser.AdditiveContext):
        self._arithmetic_chain(ctx.multiplicative(), operators(ctx))

    def visitComparison(self, ctx: RustiQParser.ComparisonContext):
        ops = operators(ctx.relOp()) if ctx.relOp() is not None else []
        self._arithmetic_chain(ctx.additive(), ops)

    def _arithmetic_chain(self, operands, ops: list[str]) -> None:
        self.visit(operands[0])
        operand_type = self.info.expr_type.get(operands[0])  # todos son del mismo tipo
        table = BINARY_F64 if operand_type == F64 else BINARY_I32
        for operand, op in zip(operands[1:], ops):
            self.visit(operand)
            self.emit(f"{wasm_type(operand_type)}.{table[op]}")

    def visitLogicalAnd(self, ctx: RustiQParser.LogicalAndContext):
        # a && b: si a es true vale b; si no, false sin evaluar b
        self._short_circuit(ctx.comparison(), on_true=None, on_false="i32.const 0")

    def visitLogicalOr(self, ctx: RustiQParser.LogicalOrContext):
        # a || b: si a es true vale true sin evaluar b; si no, vale b
        self._short_circuit(ctx.logicalAnd(), on_true="i32.const 1", on_false=None)

    def _short_circuit(self, operands, on_true: str | None, on_false: str | None) -> None:
        """Cada rama emite su constante o, si es None, evalúa el operando derecho."""
        self.visit(operands[0])
        for operand in operands[1:]:
            self.emit("if (result i32)")
            self._depth += 1
            self._emit_or_visit(on_true, operand)
            self._depth -= 1
            self.emit("else")
            self._depth += 1
            self._emit_or_visit(on_false, operand)
            self._depth -= 1
            self.emit("end")

    def _emit_or_visit(self, constant: str | None, operand) -> None:
        if constant is None:
            self.visit(operand)
        else:
            self.emit(constant)

    # --- Asignación ------------------------------------------------------------

    def visitAssignment(self, ctx: RustiQParser.AssignmentContext):
        symbol = self.info.symbol.get(ctx)
        op = ctx.assignOp().getText()
        accessors = list(place_accessors(ctx.place()))
        if not accessors:
            self._assign_local(symbol, op, ctx.expression())
        else:
            self._assign_slot(symbol, accessors, op, ctx.expression())

    def _assign_local(self, symbol, op: str, expression) -> None:
        def value() -> None:
            if op != "=":
                self.load_symbol(symbol)
            self.visit(expression)
            if op != "=":
                self._emit_compound(op, symbol.type)

        self.store_symbol(symbol, value)

    def _assign_slot(self, symbol, accessors, op: str, expression) -> None:
        """`p.a[i].b = v`: recorre las ranuras hasta la última y guarda ahí."""
        self.load_symbol(symbol)
        owner = symbol.type
        for i, (field, index) in enumerate(accessors):
            field_name = field.getText() if field is not None else None
            owner = self.emit_slot_address(owner, field_name, index)
            if i < len(accessors) - 1:
                self.emit("i32.load")  # una ranura intermedia guarda un puntero
        wt = wasm_type(owner)
        if op != "=":  # la dirección se usa dos veces: leer el valor anterior y guardar
            address = self.new_temp(StructT("_"))
            self.emit(f"local.tee {address}")
            self.emit(f"local.get {address}")
            self.emit(f"{wt}.load")
        self.visit(expression)
        if op != "=":
            self._emit_compound(op, owner)
        self.emit(f"{wt}.store")

    def _emit_compound(self, op: str, t) -> None:
        table = COMPOUND_F64 if t == F64 else COMPOUND_I32
        self.emit(f"{wasm_type(t)}.{table[op]}")
