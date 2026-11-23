"""Qué es cada identificador del programa, para mostrarlo en el editor.

Dueño: A (Yerald). No vuelve a analizar nada: lee lo que ya dejó el análisis
en `SemanticInfo` (variables, parámetros y constantes) y recorre el árbol
para las funciones, structs, enums y variantes, que se resuelven por nombre
y no quedan en `info.symbol`.

Cada pista lleva un `id`: todas las apariciones de un mismo nombre (su
declaración y sus usos) comparten el mismo. Con eso el editor puede ir a la
definición, listar las referencias y renombrar respetando los ámbitos.
"""

from dataclasses import asdict, dataclass

from antlr4 import ParserRuleContext

from rustiq.builtins import HOST_FUNCTIONS
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.semantic.info import EnumDef, FuncSig, SemanticInfo, StructDef, Symbol, SymbolKind
from rustiq.types import UNIT

# Nodos donde se declara un nombre. El resto de las anotaciones son usos.
_DECLARATIONS = (
    P.LetDeclContext,
    P.ParameterContext,
    P.ConstDeclContext,
    P.ConstLocalDeclContext,
    P.BindingPatContext,
)

_HOST_NAMES = {name for name, _ in HOST_FUNCTIONS}


@dataclass
class SymbolHint:
    line: int  # desde 1
    column: int  # desde 1
    length: int
    name: str
    kind: SymbolKind
    # El tipo, o la declaración completa si es función, struct, enum o
    # variante. None si hubo un error.
    type: str | None
    mutable: bool
    declaration: bool
    # Igual para todas las apariciones del mismo nombre declarado.
    id: str

    def to_dict(self) -> dict:
        return asdict(self)


def collect_symbols(tree: ParserRuleContext, info: SemanticInfo) -> list[SymbolHint]:
    """Un `SymbolHint` por cada aparición de un nombre, ordenados por posición."""
    hints = [_from_symbol(ctx, symbol) for ctx, symbol in info.symbol.items()]
    hints += _named_item_hints(tree, info)
    unique = {(h.line, h.column): h for h in reversed(hints)}  # gana la primera
    return sorted(unique.values(), key=lambda h: (h.line, h.column))


def _name_token(ctx: ParserRuleContext):
    """El token del nombre dentro del nodo anotado."""
    if isinstance(ctx, P.AssignmentContext):
        return ctx.place().IDENT(0).symbol
    return ctx.IDENT().symbol


def _hint(
    token, name: str, kind: SymbolKind, type_text: str | None, mutable: bool, declaration: bool, hint_id: str
) -> SymbolHint:
    return SymbolHint(
        token.line, token.column + 1, len(token.text), name, kind, type_text, mutable, declaration, hint_id
    )


# Ids de lo que se resuelve por nombre. Las variables usan el `uid` del símbolo.
def _function_id(name: str) -> str:
    return f"fn:{name}"


def _host_id(name: str) -> str:
    return f"host:{name}"


def _type_id(name: str) -> str:
    return f"type:{name}"


def _variant_id(enum: str, variant: str) -> str:
    return f"variant:{enum}::{variant}"


def _from_symbol(ctx: ParserRuleContext, symbol: Symbol) -> SymbolHint:
    type_text = str(symbol.type) if symbol.type is not None else None
    return _hint(
        _name_token(ctx), symbol.name, symbol.kind, type_text, symbol.mutable,
        isinstance(ctx, _DECLARATIONS), f"sym:{symbol.uid}",
    )


def signature(sig: FuncSig) -> str:
    """`fn suma(p: Punto) -> i32`. Sin `-> ()` cuando no devuelve nada."""
    params = ", ".join(f"{name}: {ptype}" for name, ptype in sig.params)
    ret = "" if sig.ret == UNIT else f" -> {sig.ret}"
    return f"fn {sig.name}({params}){ret}"


def struct_text(struct: StructDef) -> str:
    """La declaración, con un campo por línea."""
    if not struct.fields:
        return f"struct {struct.name} {{}}"
    fields = "".join(f"    {name}: {ftype},\n" for name, ftype in struct.fields.items())
    return f"struct {struct.name} {{\n{fields}}}"


def variant_text(enum: EnumDef, variant: str) -> str:
    payload = enum.variants[variant]
    args = f"({', '.join(str(t) for t in payload)})" if payload else ""
    return f"{variant}{args}"


def enum_text(enum: EnumDef) -> str:
    variants = "".join(f"    {variant_text(enum, v)},\n" for v in enum.variants)
    return f"enum {enum.name} {{\n{variants}}}"


def _type_name_hint(token, info: SemanticInfo, declaration: bool) -> SymbolHint | None:
    """Un nombre que puede ser struct o enum (por ejemplo, en un tipo)."""
    name = token.text
    if name in info.structs:
        text = struct_text(info.structs[name])
        return _hint(token, name, SymbolKind.STRUCT, text, False, declaration, _type_id(name))
    if name in info.enums:
        text = enum_text(info.enums[name])
        return _hint(token, name, SymbolKind.ENUM, text, False, declaration, _type_id(name))
    return None


def _enum_path_hints(node, info: SemanticInfo) -> list[SymbolHint]:
    """`Enum::Variante` en valores y patrones: una pista para cada lado."""
    enum_token, variant_token = node.IDENT(0).symbol, node.IDENT(1).symbol
    enum = info.enums.get(enum_token.text)
    if enum is None:
        return []
    hints = [_hint(enum_token, enum.name, SymbolKind.ENUM, enum_text(enum), False, False, _type_id(enum.name))]
    if variant_token.text in enum.variants:
        hints.append(_variant_hint(variant_token, enum, declaration=False))
    return hints


def _variant_hint(token, enum: EnumDef, declaration: bool) -> SymbolHint:
    variant = token.text
    text = f"{enum.name}::{variant_text(enum, variant)}"
    return _hint(token, variant, SymbolKind.VARIANT, text, False, declaration, _variant_id(enum.name, variant))


def _enum_decl_hints(node: P.EnumDeclContext, info: SemanticInfo) -> list[SymbolHint]:
    """El nombre del enum y cada una de sus variantes, como declaraciones."""
    hint = _type_name_hint(node.IDENT().symbol, info, declaration=True)
    if hint is None:
        return []
    enum = info.enums[hint.name]
    variants = [
        _variant_hint(v.IDENT().symbol, enum, declaration=True)
        for v in node.variantDecl()
        if v.IDENT().getText() in enum.variants
    ]
    return [hint, *variants]


def _hints_for_node(node, info: SemanticInfo) -> list[SymbolHint]:
    if isinstance(node, P.FunctionDeclContext):
        sig = info.functions.get(node.IDENT().getText())
        if sig is None:
            return []
        token = node.IDENT().symbol
        return [_hint(token, sig.name, SymbolKind.FUNC, signature(sig), False, True, _function_id(sig.name))]
    if isinstance(node, P.PostfixContext):
        hint = _call_hint(node, info)
        return [hint] if hint else []
    if isinstance(node, P.EnumDeclContext):
        return _enum_decl_hints(node, info)
    if isinstance(node, P.StructDeclContext):
        hint = _type_name_hint(node.IDENT().symbol, info, declaration=True)
        return [hint] if hint else []
    if isinstance(node, (P.NamedTContext, P.StructLiteralContext)):
        hint = _type_name_hint(node.IDENT().symbol, info, declaration=False)
        return [hint] if hint else []
    if isinstance(node, (P.EnumValueContext, P.EnumPatContext)):
        return _enum_path_hints(node, info)
    return []


def _named_item_hints(tree: ParserRuleContext, info: SemanticInfo) -> list[SymbolHint]:
    """Funciones, structs, enums y variantes, recorriendo el árbol."""
    hints = []
    # Recorrido con pila: las expresiones anidan muchos niveles en el árbol.
    stack = [tree]
    while stack:
        node = stack.pop()
        hints += _hints_for_node(node, info)
        stack.extend(c for c in (node.children or []) if isinstance(c, ParserRuleContext))
    return hints


def _call_hint(node: P.PostfixContext, info: SemanticInfo) -> SymbolHint | None:
    """`nombre(args)`: la misma forma que resuelve `check_call`."""
    primary = node.primary()
    is_call = (
        isinstance(primary, P.IdentPContext)
        and len(node.children) > 1
        and isinstance(node.children[1], P.CallSuffixContext)
    )
    if not is_call:
        return None
    sig = info.functions.get(primary.IDENT().getText())
    if sig is None:
        return None
    token = primary.IDENT().symbol
    if sig.name in _HOST_NAMES:
        return _hint(token, sig.name, SymbolKind.HOST, signature(sig), False, False, _host_id(sig.name))
    return _hint(token, sig.name, SymbolKind.FUNC, signature(sig), False, False, _function_id(sig.name))
