"""Generación de código de literales, operadores y variables.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos. `visitLiteral` y `visitAssignment` los
implementó A con su permiso para cerrar movimientos. Los operadores son los de
B en `b/etapa3-refs-borrows`, pasados por A, con cortocircuito en `&&` y `||`.
"""

from rustiq.codegen.gen_structs import slot_offset
from rustiq.codegen.wasm_types import wasm_type
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.check_exprs import operators
from rustiq.types import BOOL, CHAR, F64, I32, RefT, StructT

# Instrucción de cada operador binario según el tipo de los operandos.
BINARY_I32 = {
    "+": "add", "-": "sub", "*": "mul", "/": "div_s", "%": "rem_s",
    "==": "eq", "!=": "ne", "<": "lt_s", "<=": "le_s", ">": "gt_s", ">=": "ge_s",
}
BINARY_F64 = {
    "+": "add", "-": "sub", "*": "mul", "/": "div",
    "==": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge",
}

# Escalares: viven en un local, no detrás de un puntero.
SCALARS = (I32, F64, BOOL, CHAR)

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
            lname = self.declare_symbol(symbol)
            if ctx.expression() is not None:
                self.visit(ctx.expression())
                self.emit(f"local.set {lname}")

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
        """`&x` y `*r` sobre structs, tuplas y arrays: la referencia es el mismo puntero."""
        t = self.info.expr_type.get(operand)
        target = t.target if ctx.STAR() is not None and isinstance(t, RefT) else t
        if target in SCALARS:
            raise NotImplementedError("referencias a escalares (celdas con address_taken)")
        self.visit(operand)

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
        fields = self._place_fields(ctx.place())
        if not fields:
            self._assign_local(symbol, op, ctx.expression())
        else:
            self._assign_field(symbol, fields, op, ctx.expression())

    @staticmethod
    def _place_fields(place: RustiQParser.PlaceContext) -> list[str]:
        """Campos del `place` después de la variable. Los índices aún no se generan."""
        children = place.children[1:]
        if any(c.getText() == "[" for c in children):
            raise NotImplementedError("asignar a un elemento de array")
        return [c.getText() for c in children if c.getText() != "."]

    def _assign_local(self, symbol, op: str, expression) -> None:
        name = self.local_name(symbol)
        if op != "=":
            self.emit(f"local.get {name}")
        self.visit(expression)
        if op != "=":
            self._emit_compound(op, symbol.type)
        self.emit(f"local.set {name}")

    def _assign_field(self, symbol, fields: list[str], op: str, expression) -> None:
        """`p.a.b = v`: carga el puntero del último struct y guarda en su ranura."""
        self.load_symbol(symbol)
        owner = symbol.type
        for field in fields[:-1]:
            index, owner = self.field_slot(owner, field)
            self.emit(f"i32.load offset={slot_offset(index)}")
        index, field_type = self.field_slot(owner, fields[-1])
        offset, wt = slot_offset(index), wasm_type(field_type)
        if op != "=":  # el puntero se usa dos veces: leer el valor anterior y guardar
            pointer = self.new_temp(StructT("_"))
            self.emit(f"local.tee {pointer}")
            self.emit(f"local.get {pointer}")
            self.emit(f"{wt}.load offset={offset}")
        self.visit(expression)
        if op != "=":
            self._emit_compound(op, field_type)
        self.emit(f"{wt}.store offset={offset}")

    def _emit_compound(self, op: str, t) -> None:
        table = COMPOUND_F64 if t == F64 else COMPOUND_I32
        self.emit(f"{wasm_type(t)}.{table[op]}")
