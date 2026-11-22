"""Generación de código de literales, operadores y variables.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos. `visitLiteral` y `visitAssignment` los
implementó A con su permiso para cerrar movimientos.
"""

from rustiq.codegen.gen_structs import slot_offset
from rustiq.codegen.wasm_types import wasm_type
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.types import F64, StructT

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
