"""Funciones, constantes globales y llamadas: declaraciones y tipos.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas; si necesita algo de
otro mixin, llama su método público y nunca copia la lógica.

El programa se analiza en pasadas para que el orden de las declaraciones no
importe: tipos, firmas, constantes y, al final, los cuerpos.
"""

from rustiq.builtins import HOST_FUNCTIONS
from rustiq.errors import (
    E_ARG_COUNT,
    E_BAD_MAIN,
    E_BAD_RETURN,
    E_NOT_CALLABLE,
    E_REDECLARED,
    E_TYPE_MISMATCH,
    E_UNDECLARED,
    E_UNKNOWN_TYPE,
)
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.flow import block_diverges, block_tail, expression_diverges
from rustiq.semantic.info import FuncSig, SymbolKind
from rustiq.tree import call_args
from rustiq.types import (
    BOOL,
    CHAR,
    F64,
    I32,
    STRING,
    UNIT,
    ArrayT,
    RefT,
    TupleT,
    Type,
)

HOST_NAMES = {name for name, _ in HOST_FUNCTIONS}
PRIMITIVES = {"i32": I32, "f64": F64, "bool": BOOL, "char": CHAR}
MAIN = "main"


class ItemsMixin:
    def visitProgram(self, ctx: RustiQParser.ProgramContext):
        self.push_scope()
        self.define_types(ctx)  # StructsMixin: structs y enums
        self._register_host_functions()
        self._declared_fns = {}
        for item in ctx.item():
            if item.functionDecl() is not None:
                self._register_function(item.functionDecl())
            elif item.constDecl() is not None:
                self._declare_global_const(item.constDecl())
        self._check_main(ctx)
        for item in ctx.item():
            self.visit(item)
        self.pop_scope()

    # --- Registro (pasadas previas) -------------------------------------

    def _register_host_functions(self) -> None:
        for name, param_type in HOST_FUNCTIONS:
            self.info.functions[name] = FuncSig(name, [("valor", param_type)], UNIT)

    def _register_function(self, fn: RustiQParser.FunctionDeclContext) -> None:
        name = fn.IDENT().getText()
        if name in self.info.functions:
            self.error(fn.IDENT(), E_REDECLARED, f"La función '{name}' ya fue declarada")
            return
        params = []
        if fn.parameterList() is not None:
            for p in fn.parameterList().parameter():
                params.append((p.IDENT().getText(), self.resolve_type(p.type_())))
        ret = self.resolve_type(fn.type_()) if fn.type_() is not None else UNIT
        self.info.functions[name] = FuncSig(name, params, ret)
        self._declared_fns[name] = fn

    def _declare_global_const(self, decl: RustiQParser.ConstDeclContext) -> None:
        symbol = self.declare(
            decl.IDENT().getText(), self.resolve_type(decl.type_()), False, SymbolKind.CONST, decl.IDENT()
        )
        if symbol is not None:
            self.info.symbol.put(decl, symbol)

    def _check_main(self, ctx: RustiQParser.ProgramContext) -> None:
        sig = self.info.functions.get(MAIN)
        if sig is None:
            self.error(ctx, E_BAD_MAIN, "Falta la función 'main'")
        elif sig.params or sig.ret != UNIT:
            self.error(
                self._declared_fns[MAIN].IDENT(),
                E_BAD_MAIN,
                "'main' no recibe parámetros ni devuelve valor",
            )

    # --- Tipos ----------------------------------------------------------------

    def resolve_type(self, ctx: RustiQParser.TypeContext) -> Type:
        """Convierte un nodo `type` del árbol en un `Type` del contrato 2."""
        if isinstance(ctx, RustiQParser.PrimitiveTContext):
            return PRIMITIVES[ctx.primitiveType().getText()]
        if isinstance(ctx, RustiQParser.StringTContext):
            return STRING
        if isinstance(ctx, RustiQParser.ArrayTContext):
            return ArrayT(self.resolve_type(ctx.type_()), int(ctx.INT_LIT().getText()))
        if isinstance(ctx, RustiQParser.TupleTContext):
            return TupleT(tuple(self.resolve_type(t) for t in ctx.type_()))
        if isinstance(ctx, RustiQParser.RefTContext):
            return RefT(self.resolve_type(ctx.type_()), ctx.MUT() is not None)
        if isinstance(ctx, RustiQParser.RefRefTContext):
            # `&&T` es `&(&T)` y `&&mut T` es `&(&mut T)` (P10)
            return RefT(RefT(self.resolve_type(ctx.type_()), ctx.MUT() is not None), False)
        name = ctx.IDENT().getText()
        if name not in self.type_names:
            self.error(ctx, E_UNKNOWN_TYPE, f"El tipo '{name}' no existe")
            return UNIT
        return self.type_names[name]

    # --- Items ----------------------------------------------------------------

    def visitFunctionDecl(self, ctx: RustiQParser.FunctionDeclContext):
        name = ctx.IDENT().getText()
        if self._declared_fns.get(name) is not ctx:
            return  # duplicada: ya se reportó y no se analiza su cuerpo
        sig = self.info.functions[name]
        self.push_scope()
        if ctx.parameterList() is not None:
            for p, (_, ptype) in zip(ctx.parameterList().parameter(), sig.params):
                symbol = self.declare(p.IDENT().getText(), ptype, p.MUT() is not None, SymbolKind.PARAM, p.IDENT())
                if symbol is not None:
                    self.info.symbol.put(p, symbol)
                    self.track_symbol(symbol)
        self.fn_ret, self.loop_depth = sig.ret, 0
        body_type = self.visit(ctx.block())
        if block_tail(ctx.block()) is not None:
            self.check_returned_ref(block_tail(ctx.block()))
        self.pop_scope()
        self._check_function_result(ctx, sig, body_type)

    def _check_function_result(self, ctx, sig: FuncSig, body_type: Type | None) -> None:
        block = ctx.block()
        tail = block_tail(block)
        if tail is not None and expression_diverges(tail):
            return  # `match` como valor final con `return` en todos los brazos
        if tail is not None:
            self.mismatch(tail, E_BAD_RETURN, sig.ret, body_type, f"El valor final de '{sig.name}'")
        elif sig.ret != UNIT and not block_diverges(block):
            self.error(
                block.RBRACE(), E_BAD_RETURN, f"'{sig.name}' debe devolver {sig.ret} en todos sus caminos"
            )

    def visitConstDecl(self, ctx: RustiQParser.ConstDeclContext):
        symbol = self.info.symbol.get(ctx)
        actual = self.visit(ctx.expression())
        if symbol is not None:
            self.mismatch(
                ctx.expression(), E_TYPE_MISMATCH, symbol.type, actual,
                f"La constante '{symbol.name}'",
            )

    def visitStructDecl(self, ctx):
        return None  # ya se definió en la pasada de tipos

    def visitEnumDecl(self, ctx):
        return None

    # --- Llamadas -------------------------------------------------------------

    def check_call(self, callee: RustiQParser.IdentPContext, call: RustiQParser.CallSuffixContext):
        """Resuelve `nombre(args)`: existencia, número y tipo de argumentos."""
        name = callee.IDENT().getText()
        args = call_args(call)
        mark = self.borrow_mark()
        # Se visitan siempre para ver sus errores. Imprimir no mueve: `print_str(s)`
        # deja `s` disponible, porque el host solo lee el String.
        arg_types = self.visit_and_consume(args, moves=name not in HOST_NAMES)
        sig = self.info.functions.get(name)
        if sig is not None and not self.may_hold_ref(sig.ret):
            # Los `&`/`&mut` de los argumentos terminan al volver: el resultado no
            # puede llevárselos. Así `f(&mut c) + f(&mut c)` es válido.
            self.release_temporary_borrows(mark)
        if sig is None:
            if self.lookup(name) is not None:
                self.error(callee, E_NOT_CALLABLE, f"'{name}' no es una función")
            else:
                self.error(callee, E_UNDECLARED, f"La función '{name}' no existe")
            return None
        if len(args) != len(sig.params):
            self.error(
                callee, E_ARG_COUNT,
                f"'{name}' espera {len(sig.params)} argumento(s) y recibió {len(args)}",
            )
        else:
            for arg, actual, (pname, ptype) in zip(args, arg_types, sig.params):
                self.mismatch(arg, E_TYPE_MISMATCH, ptype, actual, f"Argumento '{pname}' de '{name}'")
        return sig.ret
