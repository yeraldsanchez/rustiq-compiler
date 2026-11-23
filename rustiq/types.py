"""Tipos del lenguaje.

Los usan el análisis semántico y el backend. La regla de copia vive
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


def is_scalar(t: Type) -> bool:
    """True si el valor vive directo en un local (docs/memoria.md), no detrás de un puntero.

    Son los que necesitan una celda en el heap cuando se les aplica `&`.
    """
    return t in (I32, F64, BOOL, CHAR) or isinstance(t, RefT)


def is_copy(t: Type) -> bool:
    """Regla única de copia: solo los escalares y `&T` son Copy.

    - i32, f64, bool, char y () son Copy.
    - &T es Copy, &mut T no.
    - Todo lo que vive en el heap se mueve: String, arrays, tuplas, structs y
      enums. Así copiar un valor nunca necesita memcpy (más estricto que Rust).
    """
    if t in (I32, F64, BOOL, CHAR, UNIT):
        return True
    if isinstance(t, RefT):
        return not t.mutable
    return False
