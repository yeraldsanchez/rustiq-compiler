"""Apoyo para las pruebas: compilar, analizar y ejecutar programas cortos.

`StandInExprs` y `StandInGen` implementan lo mínimo de literales, identificadores,
operadores, `let` y asignación simple, para probar cada parte del análisis y
del codegen por separado. Las pruebas que necesitan programas completos se
marcan con `necesita_expresiones` y solo corren si el compilador ya tiene
literales y operadores en ambos visitors.

Convención que cumple todo `visitX` de expresión del Analyzer: devuelve su Type.
En el Emitter deja su valor en la pila de Wasm.
"""

import pytest
from antlr4.tree.Tree import TerminalNode
from wasmtime import Engine, FuncType, Linker, Module, Store, ValType

from rustiq.codegen.emitter import Emitter
from rustiq.errors import E_UNDECLARED
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.pipeline import assemble, parse_source
from rustiq.semantic.analyzer import Analyzer
from rustiq.types import BOOL, CHAR, F64, I32

from rustiq.generated.RustiQVisitor import RustiQVisitor

# True cuando hay literales y operadores en ambos visitors (el visitor generado
# ya trae versiones vacías). Basta con mirar literales y sumas.
EXPRESIONES_LISTAS = all(
    getattr(visitor, rule) is not getattr(RustiQVisitor, rule)
    for visitor in (Analyzer, Emitter)
    for rule in ("visitLiteral", "visitAdditive")
)
necesita_expresiones = pytest.mark.skipif(not EXPRESIONES_LISTAS, reason="faltan literales u operadores")

PROGRAMA_MINIMO = "fn auxiliar() {}\nfn main() { auxiliar() }"


# --- Analyzer ------------------------------------------------------------------


class StandInExprs:
    def visitLiteral(self, ctx: P.LiteralContext):
        if ctx.INT_LIT():
            return I32
        if ctx.FLOAT_LIT():
            return F64
        if ctx.CHAR_LIT():
            return CHAR
        return BOOL  # true / false

    def visitIdentP(self, ctx: P.IdentPContext):
        symbol = self.lookup(ctx.IDENT().getText())
        if symbol is None:
            self.error(ctx, E_UNDECLARED, f"'{ctx.IDENT().getText()}' no está declarado")
            return None
        self.info.symbol.put(ctx, symbol)
        return symbol.type

    def visitParenP(self, ctx: P.ParenPContext):
        return self.visit(ctx.expression())

    def visitUnary(self, ctx: P.UnaryContext):
        t = self.visit(ctx.postfix())
        if t is not None:
            self.info.expr_type.put(ctx.postfix(), t)
        return BOOL if ctx.BANG() else t

    def _binary(self, ctx, operands, result=None):
        types = [self.visit(o) for o in operands]
        for operand, t in zip(operands, types):
            if t is not None:
                self.info.expr_type.put(operand, t)
        return result or types[0]

    def visitMultiplicative(self, ctx):
        return self._binary(ctx, ctx.unary())

    def visitAdditive(self, ctx):
        return self._binary(ctx, ctx.multiplicative())

    def visitComparison(self, ctx):
        return self._binary(ctx, ctx.additive(), BOOL if ctx.relOp() else None)

    def visitLogicalAnd(self, ctx):
        operands = ctx.comparison()
        return self._binary(ctx, operands, BOOL if len(operands) > 1 else None)

    def visitLogicalOr(self, ctx):
        operands = ctx.logicalAnd()
        return self._binary(ctx, operands, BOOL if len(operands) > 1 else None)

    def visitLetDecl(self, ctx: P.LetDeclContext):
        init = self.visit(ctx.expression()) if ctx.expression() else None
        declared = self.resolve_type(ctx.type_()) if ctx.type_() else init
        symbol = self.declare(ctx.IDENT().getText(), declared, ctx.MUT() is not None, "local", ctx.IDENT())
        self.info.symbol.put(ctx, symbol)

    def visitAssignment(self, ctx: P.AssignmentContext):
        self.info.symbol.put(ctx, self.lookup(ctx.place().IDENT(0).getText()))
        self.visit(ctx.expression())


class TestAnalyzer(StandInExprs, Analyzer):
    __test__ = False


# --- Emitter -------------------------------------------------------------------

BINARY = {"+": "add", "-": "sub", "*": "mul", "/": "div_s", "%": "rem_s"}
COMPARE_I32 = {"==": "eq", "!=": "ne", "<": "lt_s", "<=": "le_s", ">": "gt_s", ">=": "ge_s"}
COMPARE_F64 = {"==": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge"}


def _operators(ctx) -> list[str]:
    return [c.getText() for c in ctx.children if isinstance(c, TerminalNode)]


class StandInGen:
    def visitLiteral(self, ctx: P.LiteralContext):
        text = ctx.getText()
        if ctx.INT_LIT():
            self.emit(f"i32.const {text}")
        elif ctx.FLOAT_LIT():
            self.emit(f"f64.const {text}")
        elif ctx.CHAR_LIT():
            self.emit(f"i32.const {ord(text[1])}")
        else:
            self.emit(f"i32.const {1 if text == 'true' else 0}")

    def visitIdentP(self, ctx: P.IdentPContext):
        self.load_symbol(self.info.symbol.get(ctx))

    def visitParenP(self, ctx: P.ParenPContext):
        self.visit(ctx.expression())

    def visitUnary(self, ctx: P.UnaryContext):
        if ctx.MINUS():
            t = self.info.expr_type.get(ctx.postfix())
            if t == F64:
                self.visit(ctx.postfix())
                self.emit("f64.neg")
            else:
                self.emit("i32.const 0")
                self.visit(ctx.postfix())
                self.emit("i32.sub")
        elif ctx.BANG():
            self.visit(ctx.postfix())
            self.emit("i32.eqz")
        else:
            self.visit(ctx.postfix())

    def _chain(self, operands, operators, table):
        self.visit(operands[0])
        for operand, op in zip(operands[1:], operators):
            self.visit(operand)
            t = self.info.expr_type.get(operands[0])
            kind, name = ("f64", table[op].removesuffix("_s")) if t == F64 else ("i32", table[op])
            self.emit(f"{kind}.{name}")

    def visitMultiplicative(self, ctx):
        self._chain(ctx.unary(), _operators(ctx), BINARY)

    def visitAdditive(self, ctx):
        self._chain(ctx.multiplicative(), _operators(ctx), BINARY)

    def visitComparison(self, ctx):
        operands = ctx.additive()
        if not ctx.relOp():
            return self.visit(operands[0])
        table = COMPARE_F64 if self.info.expr_type.get(operands[0]) == F64 else COMPARE_I32
        self._chain(operands, [ctx.relOp().getText()], table)

    def visitLogicalAnd(self, ctx):
        self._chain(ctx.comparison(), ["&&"] * (len(ctx.comparison()) - 1), {"&&": "and"})

    def visitLogicalOr(self, ctx):
        self._chain(ctx.logicalAnd(), ["||"] * (len(ctx.logicalAnd()) - 1), {"||": "or"})

    def visitLetDecl(self, ctx: P.LetDeclContext):
        name = self.declare_symbol(self.info.symbol.get(ctx))
        if ctx.expression():
            self.visit(ctx.expression())
            self.emit(f"local.set {name}")

    def visitAssignment(self, ctx: P.AssignmentContext):
        name = self.local_name(self.info.symbol.get(ctx))
        op = ctx.assignOp().getText()
        if op != "=":
            self.emit(f"local.get {name}")
        self.visit(ctx.expression())
        if op != "=":
            self.emit(f"i32.{BINARY[op[0]]}")
        self.emit(f"local.set {name}")


class TestEmitter(StandInGen, Emitter):
    __test__ = False


# --- Pipeline de pruebas --------------------------------------------------------


def analyze(source: str):
    """(árbol, info, errores) con las expresiones de prueba."""
    tree, syntax_errors = parse_source(source)
    assert syntax_errors == [], syntax_errors
    info, errors = TestAnalyzer().analyze(tree)
    return tree, info, errors


def compile_wat(source: str) -> str:
    tree, info, errors = analyze(source)
    assert errors == [], errors
    return TestEmitter(info).generate(tree)


def compile_wasm(source: str) -> bytes:
    return assemble(compile_wat(source))


def error_codes(source: str) -> list[tuple[str, int, int]]:
    """(código, línea, columna) de cada error semántico."""
    _, _, errors = analyze(source)
    return [(e.code, e.line, e.column) for e in errors]


def run(source: str) -> list[str]:
    """Compila y ejecuta con wasmtime; devuelve una línea por cada print_*."""
    out: list[str] = []
    engine = Engine()
    store = Store(engine)
    linker = Linker(engine)
    hosts = {
        "print_i32": (ValType.i32(), str),
        "print_f64": (ValType.f64(), str),
        "print_bool": (ValType.i32(), lambda v: "true" if v else "false"),
        "print_char": (ValType.i32(), chr),
    }
    for name, (param, fmt) in hosts.items():
        linker.define_func("env", name, FuncType([param], []), lambda v, fmt=fmt: out.append(fmt(v)))
    linker.define_func("env", "print_str", FuncType([ValType.i32()], []), lambda v: out.append("<str>"))
    instance = linker.instantiate(store, Module(engine, compile_wasm(source)))
    instance.exports(store)["main"](store)
    return out
