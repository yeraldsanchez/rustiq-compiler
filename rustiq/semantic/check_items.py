"""Funciones, constantes, structs y tuplas: declaraciones y tipos.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas; si necesita algo de
otro mixin, llama su método público y nunca copia la lógica.

Por ahora registra las firmas de las funciones (`info.functions`), que es lo que
el emisor base necesita para generar el módulo.
"""

from rustiq.errors import E_REDECLARED, E_UNKNOWN_TYPE
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.info import FuncSig
from rustiq.types import (
    BOOL,
    CHAR,
    F64,
    I32,
    STRING,
    UNIT,
    ArrayT,
    EnumT,
    RefT,
    StructT,
    TupleT,
    Type,
)

PRIMITIVES = {"i32": I32, "f64": F64, "bool": BOOL, "char": CHAR}


class ItemsMixin:
    def visitProgram(self, ctx: RustiQParser.ProgramContext):
        type_names = self._collect_type_names(ctx)
        for item in ctx.item():
            fn = item.functionDecl()
            if fn is not None:
                self._register_function(fn, type_names)
        return self.visitChildren(ctx)

    def _collect_type_names(self, ctx) -> dict[str, Type]:
        """Nombres de structs y enums declarados, para resolver `NamedT`."""
        names: dict[str, Type] = {}
        for item in ctx.item():
            if item.structDecl() is not None:
                name = item.structDecl().IDENT().getText()
                names.setdefault(name, StructT(name))
            elif item.enumDecl() is not None:
                name = item.enumDecl().IDENT().getText()
                names.setdefault(name, EnumT(name))
        return names

    def _register_function(self, fn: RustiQParser.FunctionDeclContext, type_names) -> None:
        name = fn.IDENT().getText()
        if name in self.info.functions:
            self.error(fn.IDENT(), E_REDECLARED, f"La función '{name}' ya fue declarada")
            return
        params = []
        if fn.parameterList() is not None:
            for p in fn.parameterList().parameter():
                params.append((p.IDENT().getText(), self.resolve_type(p.type_(), type_names)))
        ret = self.resolve_type(fn.type_(), type_names) if fn.type_() is not None else UNIT
        self.info.functions[name] = FuncSig(name, params, ret)

    def resolve_type(self, ctx: RustiQParser.TypeContext, type_names) -> Type:
        """Convierte un nodo `type` del árbol en un `Type` del contrato 2."""
        if isinstance(ctx, RustiQParser.PrimitiveTContext):
            return PRIMITIVES[ctx.primitiveType().getText()]
        if isinstance(ctx, RustiQParser.StringTContext):
            return STRING
        if isinstance(ctx, RustiQParser.ArrayTContext):
            return ArrayT(self.resolve_type(ctx.type_(), type_names), int(ctx.INT_LIT().getText()))
        if isinstance(ctx, RustiQParser.TupleTContext):
            return TupleT(tuple(self.resolve_type(t, type_names) for t in ctx.type_()))
        if isinstance(ctx, RustiQParser.RefTContext):
            return RefT(self.resolve_type(ctx.type_(), type_names), ctx.MUT() is not None)
        if isinstance(ctx, RustiQParser.RefRefTContext):
            # `&&T` es `&(&T)` y `&&mut T` es `&(&mut T)` (P10)
            return RefT(RefT(self.resolve_type(ctx.type_(), type_names), ctx.MUT() is not None), False)
        name = ctx.IDENT().getText()
        if name not in type_names:
            self.error(ctx, E_UNKNOWN_TYPE, f"El tipo '{name}' no existe")
            return UNIT
        return type_names[name]
