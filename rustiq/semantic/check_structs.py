"""Structs y tuplas: declaración, literal y acceso a campo.

Dueño: A (Yerald). Implementa solo los `visitX` de sus reglas.
"""

from rustiq.errors import (
    E_BAD_OPERAND,
    E_MISSING_FIELD,
    E_REDECLARED,
    E_TYPE_MISMATCH,
    E_UNKNOWN_FIELD,
    E_UNKNOWN_TYPE,
)
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.info import EnumDef, StructDef
from rustiq.types import EnumT, RefT, StructT, TupleT


class StructsMixin:
    # --- Definiciones (pasada previa de visitProgram) -------------------

    def define_types(self, program: RustiQParser.ProgramContext) -> None:
        """Registra los nombres de structs y enums y luego sus campos y variantes."""
        decls = []
        for item in program.item():
            decl = item.structDecl() or item.enumDecl()
            if decl is None:
                continue
            name = decl.IDENT().getText()
            if name in self.type_names:
                self.error(decl.IDENT(), E_REDECLARED, f"El tipo '{name}' ya fue declarado")
                continue
            is_struct = item.structDecl() is not None
            self.type_names[name] = StructT(name) if is_struct else EnumT(name)
            decls.append(decl)
        for decl in decls:
            if isinstance(decl, RustiQParser.StructDeclContext):
                self._define_struct(decl)
            else:
                self._define_enum(decl)

    def _define_struct(self, decl: RustiQParser.StructDeclContext) -> None:
        fields = {}
        for f in decl.fieldDecl():
            fname = f.IDENT().getText()
            if fname in fields:
                self.error(f.IDENT(), E_REDECLARED, f"El campo '{fname}' está repetido")
                continue
            fields[fname] = self.resolve_type(f.type_())
        self.info.structs[decl.IDENT().getText()] = StructDef(decl.IDENT().getText(), fields)

    def _define_enum(self, decl: RustiQParser.EnumDeclContext) -> None:
        variants = {}
        for v in decl.variantDecl():
            vname = v.IDENT().getText()
            if vname in variants:
                self.error(v.IDENT(), E_REDECLARED, f"La variante '{vname}' está repetida")
                continue
            payload = v.typeList().type_() if v.typeList() is not None else []
            variants[vname] = tuple(self.resolve_type(t) for t in payload)
        self.info.enums[decl.IDENT().getText()] = EnumDef(decl.IDENT().getText(), variants)

    # --- Expresiones ----------------------------------------------------------

    def visitStructLiteral(self, ctx: RustiQParser.StructLiteralContext):
        name = ctx.IDENT().getText()
        definition = self.info.structs.get(name)
        inits = ctx.fieldInit()
        types = [self.visit(fi.expression()) for fi in inits]  # siempre, para ver sus errores
        if definition is None:
            self.error(ctx.IDENT(), E_UNKNOWN_TYPE, f"El struct '{name}' no existe")
            return None
        seen = set()
        for fi, actual in zip(inits, types):
            fname = fi.IDENT().getText()
            if fname not in definition.fields:
                self.error(fi.IDENT(), E_UNKNOWN_FIELD, f"'{name}' no tiene el campo '{fname}'")
            elif fname in seen:
                self.error(fi.IDENT(), E_REDECLARED, f"El campo '{fname}' está repetido")
            else:
                seen.add(fname)
                self.mismatch(
                    fi.expression(), E_TYPE_MISMATCH, definition.fields[fname], actual,
                    f"El campo '{fname}' de '{name}'",
                )
        missing = [f for f in definition.fields if f not in seen]
        if missing:
            self.error(ctx.IDENT(), E_MISSING_FIELD, f"Faltan campos en '{name}': {', '.join(missing)}")
        result = StructT(name)
        self.info.expr_type.put(ctx, result)
        return result

    def visitTupleLiteral(self, ctx: RustiQParser.TupleLiteralContext):
        elems = [self.visit(e) for e in ctx.expression()]
        if any(e is None for e in elems):
            return None
        result = TupleT(tuple(elems))
        self.info.expr_type.put(ctx, result)
        return result

    def visitFieldSuffix(self, ctx: RustiQParser.FieldSuffixContext):
        operand = self.info.expr_type.get(ctx)
        base = operand.target if isinstance(operand, RefT) else operand  # auto-deref de un nivel
        field = ctx.IDENT().getText()
        if not isinstance(base, StructT):
            self.error(ctx.IDENT(), E_BAD_OPERAND, f"El tipo {operand} no tiene campos")
            return None
        fields = self.info.structs[base.name].fields
        if field not in fields:
            self.error(ctx.IDENT(), E_UNKNOWN_FIELD, f"'{base.name}' no tiene el campo '{field}'")
            return None
        return fields[field]
