"""Contrato 2: tipos del lenguaje.

Los usan el análisis semántico (A y B) y el backend. La regla de copia vive
solo en `is_copy`.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PrimitiveT:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class ArrayT:
    elem: "Type"
    size: int

    def __str__(self) -> str:
        return f"[{self.elem}; {self.size}]"


@dataclass(frozen=True)
class TupleT:
    elems: tuple["Type", ...]

    def __str__(self) -> str:
        return "(" + ", ".join(str(e) for e in self.elems) + ")"


@dataclass(frozen=True)
class RefT:
    target: "Type"
    mutable: bool

    def __str__(self) -> str:
        return f"&{'mut ' if self.mutable else ''}{self.target}"


@dataclass(frozen=True)
class StructT:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class EnumT:
    name: str

    def __str__(self) -> str:
        return self.name


Type = PrimitiveT | ArrayT | TupleT | RefT | StructT | EnumT

# Singletons
I32 = PrimitiveT("i32")
F64 = PrimitiveT("f64")
BOOL = PrimitiveT("bool")
CHAR = PrimitiveT("char")
STRING = PrimitiveT("String")
UNIT = TupleT(())  # tipo de las funciones sin valor de retorno: ()


def is_copy(t: Type) -> bool:
    """Regla única de copia (decisión G1, igual que Rust).

    - i32, f64, bool, char y () son Copy.
    - &T es Copy, &mut T no.
    - Array o tupla es Copy solo si todos sus elementos lo son.
    - String, structs y enums se mueven.
    """
    if t in (I32, F64, BOOL, CHAR):
        return True
    if isinstance(t, RefT):
        return not t.mutable
    if isinstance(t, ArrayT):
        return is_copy(t.elem)
    if isinstance(t, TupleT):
        return all(is_copy(e) for e in t.elems)
    return False
