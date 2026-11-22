"""Qué es cada identificador del programa, para mostrarlo en el editor.

Dueño: A (Yerald). No vuelve a analizar nada: lee lo que ya dejó el análisis
en `SemanticInfo` (variables, parámetros y constantes) y recorre el árbol
para las funciones, structs, enums y variantes, que se resuelven por nombre
y no quedan en `info.symbol`.
"""

from dataclasses import asdict, dataclass

from antlr4 import ParserRuleContext

from rustiq.builtins import HOST_FUNCTIONS
from rustiq.generated.RustiQParser import RustiQParser as P
from rustiq.semantic.info import EnumDef, FuncSig, SemanticInfo, StructDef, Symbol
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
    kind: str  # "local" | "param" | "const" | "func" | "host" | "struct" | "enum" | "variant"
    # El tipo, o la declaración completa si es función, struct, enum o
    # variante. None si hubo un error.
    type: str | None
    mutable: bool
    declaration: bool

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


def _hint(token, name: str, kind: str, type_text: str | None, mutable: bool, declaration: bool) -> SymbolHint:
    return SymbolHint(token.line, token.column + 1, len(token.text), name, kind, type_text, mutable, declaration)


def _from_symbol(ctx: ParserRuleContext, symbol: Symbol) -> SymbolHint:
    type_text = str(symbol.type) if symbol.type is not None else None
    return _hint(
        _name_token(ctx), symbol.name, symbol.kind, type_text, symbol.mutable,
        isinstance(ctx, _DECLARATIONS),
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
        return _hint(token, name, "struct", struct_text(info.structs[name]), False, declaration)
    if name in info.enums:
        return _hint(token, name, "enum", enum_text(info.enums[name]), False, declaration)
    return None


def _enum_path_hints(node, info: SemanticInfo) -> list[SymbolHint]:
    """`Enum::Variante` en valores y patrones: una pista para cada lado."""
    enum_token, variant_token = node.IDENT(0).symbol, node.IDENT(1).symbol
    enum = info.enums.get(enum_token.text)
    if enum is None:
        return []
    hints = [_hint(enum_token, enum.name, "enum", enum_text(enum), False, False)]
    if variant_token.text in enum.variants:
        text = f"{enum.name}::{variant_text(enum, variant_token.text)}"
        hints.append(_hint(variant_token, variant_token.text, "variant", text, False, False))
    return hints


def _hints_for_node(node, info: SemanticInfo) -> list[SymbolHint]:
    if isinstance(node, P.FunctionDeclContext):
        sig = info.functions.get(node.IDENT().getText())
        return [_hint(node.IDENT().symbol, sig.name, "func", signature(sig), False, True)] if sig else []
    if isinstance(node, P.PostfixContext):
        hint = _call_hint(node, info)
        return [hint] if hint else []
    if isinstance(node, (P.StructDeclContext, P.EnumDeclContext)):
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
    kind = "host" if sig.name in _HOST_NAMES else "func"
    return _hint(primary.IDENT().symbol, sig.name, kind, signature(sig), False, False)
