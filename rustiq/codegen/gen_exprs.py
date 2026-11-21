"""Generación de código de literales, operadores, variables y asignaciones (Carril B)."""

from antlr4.tree.Tree import TerminalNode

from rustiq.generated.RustiQParser import RustiQParser
from rustiq.types import F64, I32, RefT

BINARY_OPS = {"+": "add", "-": "sub", "*": "mul", "/": "div_s", "%": "rem_s"}
COMPARE_I32 = {"==": "eq", "!=": "ne", "<": "lt_s", "<=": "le_s", ">": "gt_s", ">=": "ge_s"}
COMPARE_F64 = {"==": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge"}


def _decode_char(raw: str) -> int:
    inner = raw[1:-1]
    escapes = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "'": "'", "\\": "\\"}
    if inner.startswith("\\") and len(inner) >= 2:
        return ord(escapes.get(inner[1], inner[1]))
    return ord(inner[0])


class ExprsGenMixin:
    def visitLiteral(self, ctx: RustiQParser.LiteralContext):
        text = ctx.getText()
        if ctx.INT_LIT() is not None:
            self.emit(f"i32.const {text}")
        elif ctx.FLOAT_LIT() is not None:
            self.emit(f"f64.const {text}")
        elif ctx.CHAR_LIT() is not None:
            self.emit(f"i32.const {_decode_char(text)}")
        elif ctx.STRING_LIT() is not None:
            self.emit_string_literal(text)
        else:
            self.emit(f"i32.const {1 if text == 'true' else 0}")

    def visitIdentP(self, ctx: RustiQParser.IdentPContext):
        symbol = self.info.symbol.get(ctx)
        if symbol is not None and self.is_boxed_scalar(symbol):
            self.emit_box_load(symbol)
        else:
            self.load_symbol(symbol)

    def visitParenP(self, ctx: RustiQParser.ParenPContext):
        self.visit(ctx.expression())

    def visitUnary(self, ctx: RustiQParser.UnaryContext):
        if ctx.AMP() is not None:
            self.emit_borrow(ctx)
            return
        if ctx.STAR() is not None:
            self.emit_deref(ctx)
            return
        if ctx.MINUS() is not None:
            t = self.info.expr_type.get(ctx.postfix())
            if t == F64:
                self.visit(ctx.postfix())
                self.emit("f64.neg")
            else:
                self.emit("i32.const 0")
                self.visit(ctx.postfix())
                self.emit("i32.sub")
            return
        if ctx.BANG() is not None:
            self.visit(ctx.postfix())
            self.emit("i32.eqz")
            return
        self.visit(ctx.postfix())

    def _emit_binary_chain(self, operands, operators: list[str], table: dict[str, str]):
        self.visit(operands[0])
        t = self.info.expr_type.get(operands[0])
        for operand, op in zip(operands[1:], operators):
            self.visit(operand)
            if t == F64:
                self.emit(f"f64.{table[op].removesuffix('_s')}")
            else:
                self.emit(f"i32.{table[op]}")

    def visitMultiplicative(self, ctx: RustiQParser.MultiplicativeContext):
        ops = [c.getText() for c in ctx.children if isinstance(c, TerminalNode)]
        self._emit_binary_chain(ctx.unary(), ops, BINARY_OPS)

    def visitAdditive(self, ctx: RustiQParser.AdditiveContext):
        ops = [c.getText() for c in ctx.children if isinstance(c, TerminalNode)]
        self._emit_binary_chain(ctx.multiplicative(), ops, BINARY_OPS)

    def visitComparison(self, ctx: RustiQParser.ComparisonContext):
        operands = ctx.additive()
        if ctx.relOp() is None:
            self.visit(operands[0])
            return
        t = self.info.expr_type.get(operands[0])
        table = COMPARE_F64 if t == F64 else COMPARE_I32
        self._emit_binary_chain(operands, [ctx.relOp().getText()], table)

    def visitLogicalAnd(self, ctx: RustiQParser.LogicalAndContext):
        operands = ctx.comparison()
        if len(operands) == 1:
            self.visit(operands[0])
            return
        self._emit_binary_chain(operands, ["&&"] * (len(operands) - 1), {"&&": "and"})

    def visitLogicalOr(self, ctx: RustiQParser.LogicalOrContext):
        operands = ctx.logicalAnd()
        if len(operands) == 1:
            self.visit(operands[0])
            return
        self._emit_binary_chain(operands, ["||"] * (len(operands) - 1), {"||": "or"})

    def visitLetDecl(self, ctx: RustiQParser.LetDeclContext):
        symbol = self.info.symbol.get(ctx)
        lname = self.declare_symbol(symbol)
        if self.is_boxed_scalar(symbol):
            self.emit_box_alloc(symbol)
            if ctx.expression() is not None:
                self.visit(ctx.expression())
                self.emit_box_store(symbol)
        elif ctx.expression() is not None:
            self.visit(ctx.expression())
            self.emit(f"local.set {lname}")

    def visitAssignment(self, ctx: RustiQParser.AssignmentContext):
        symbol = self.info.symbol.get(ctx)
        place = ctx.place()
        op = ctx.assignOp().getText()

        if place.getChildCount() == 1:
            lname = self.local_name(symbol)
            if self.is_boxed_scalar(symbol):
                if op != "=":
                    self.emit_box_load(symbol)
                self.visit(ctx.expression())
                if op != "=":
                    inst = BINARY_OPS[op[0]].removesuffix("_s") if symbol.type == F64 else BINARY_OPS[op[0]]
                    self.emit(f"{'f64' if symbol.type == F64 else 'i32'}.{inst}")
                self.emit_box_store(symbol)
            else:
                if op != "=":
                    self.emit(f"local.get {lname}")
                self.visit(ctx.expression())
                if op != "=":
                    inst = BINARY_OPS[op[0]].removesuffix("_s") if symbol.type == F64 else BINARY_OPS[op[0]]
                    self.emit(f"{'f64' if symbol.type == F64 else 'i32'}.{inst}")
                self.emit(f"local.set {lname}")
            return

        self.emit(f"local.get {self.local_name(symbol)}")
        current_type = symbol.type
        i = 1
        while i < place.getChildCount():
            if isinstance(current_type, RefT):
                current_type = current_type.target
            token_text = place.getChild(i).getText()
            is_last = (token_text == "." and i + 2 == place.getChildCount()) or (
                token_text == "[" and i + 3 == place.getChildCount()
            )
            if token_text == ".":
                slot_idx, field_type = self.field_slot(current_type, place.getChild(i + 1).getText())
                if slot_idx > 0:
                    self.emit(f"i32.const {slot_idx * 8}")
                    self.emit("i32.add")
                if not is_last:
                    self.emit("i32.load")
                current_type = field_type
                i += 2
            elif token_text == "[":
                self.visit(place.getChild(i + 1))
                self.emit("i32.const 8")
                self.emit("i32.mul")
                self.emit("i32.add")
                if not is_last:
                    self.emit("i32.load")
                current_type = current_type.elem
                i += 3

        addr_tmp = self.new_temp(I32)
        self.emit(f"local.set {addr_tmp}")

        self.emit(f"local.get {addr_tmp}")
        if op != "=":
            self.emit(f"local.get {addr_tmp}")
            self.emit("f64.load" if current_type == F64 else "i32.load")
        self.visit(ctx.expression())
        if op != "=":
            inst = BINARY_OPS[op[0]].removesuffix("_s") if current_type == F64 else BINARY_OPS[op[0]]
            self.emit(f"{'f64' if current_type == F64 else 'i32'}.{inst}")
        self.emit("f64.store" if current_type == F64 else "i32.store")
