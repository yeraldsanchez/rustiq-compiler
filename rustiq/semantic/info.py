"""Contrato 3: resultado del análisis semántico.

Es la frontera entre el análisis (A y B) y el codegen. El codegen lee solo
esto y nunca vuelve a inferir tipos.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Generic, TypeVar

from rustiq.types import Type

T = TypeVar("T")


class NodeProperty(Generic[T]):
    """Anota nodos del árbol de ANTLR sin construir un AST.

    Equivale al `ParseTreeProperty` de Java, que el runtime de Python no trae.
    Los contextos de ANTLR se comparan por identidad, así que sirven de clave.
    """

    def __init__(self) -> None:
        self._values: dict[Any, T] = {}

    def put(self, node: Any, value: T) -> None:
        self._values[node] = value

    def get(self, node: Any) -> T | None:
        return self._values.get(node)

    def __contains__(self, node: Any) -> bool:
        return node in self._values

    def items(self) -> list[tuple[Any, T]]:
        """Pares (nodo, valor) en el orden en que se anotaron."""
        return list(self._values.items())


class SymbolKind(StrEnum):
    """Qué es un nombre. Es un `str`: se compara y se serializa como su texto."""

    LOCAL = "local"
    PARAM = "param"
    CONST = "const"
    FUNC = "func"
    HOST = "host"  # función del host (`print_*`)
    STRUCT = "struct"
    ENUM = "enum"
    VARIANT = "variant"


# Variables dueñas de su valor: se pueden mover, asignar y prestar.
VARIABLE_KINDS = (SymbolKind.LOCAL, SymbolKind.PARAM)


@dataclass
class Symbol:
    uid: int  # único en todo el programa, resuelve el sombreado
    name: str
    type: Type
    mutable: bool
    kind: SymbolKind  # LOCAL, PARAM o CONST
    address_taken: bool = False  # True si se le aplica & y es escalar


@dataclass
class StructDef:
    name: str
    fields: dict[str, Type]  # en orden de declaración


@dataclass
class EnumDef:
    name: str
    variants: dict[str, tuple[Type, ...]]  # nombre -> tipos del payload; el tag es el índice

    def tag_of(self, variant: str) -> int:
        return list(self.variants).index(variant)


@dataclass
class FuncSig:
    name: str
    params: list[tuple[str, Type]]
    ret: Type


@dataclass
class SemanticInfo:
    expr_type: NodeProperty[Type] = field(default_factory=NodeProperty)  # ctx de expresión -> Type
    symbol: NodeProperty[Symbol] = field(default_factory=NodeProperty)  # ctx de identificador -> Symbol
    structs: dict[str, StructDef] = field(default_factory=dict)
    enums: dict[str, EnumDef] = field(default_factory=dict)
    functions: dict[str, FuncSig] = field(default_factory=dict)
