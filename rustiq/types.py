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

# Alias for the String primitive type (used by the parser and type checker)


# Helper utilities for reference types

def is_shared_ref(t: Type) -> bool:
    """Return True if *t* is a shared reference (`&T`).
    Shared references are represented by `RefT` with ``mutable=False``.
    """
    return isinstance(t, RefT) and not t.mutable


def is_mutable_ref(t: Type) -> bool:
    """Return True if *t* is a mutable reference (`&mut T`).
    Mutable references are represented by `RefT` with ``mutable=True``.
    """
    return isinstance(t, RefT) and t.mutable

I32 = PrimitiveT("i32")
F64 = PrimitiveT("f64")
BOOL = PrimitiveT("bool")
CHAR = PrimitiveT("char")
STRING = PrimitiveT("String")
# Alias for the primitive String type used throughout the compiler
String = STRING

# Unit type – represents functions that return no value ("()")
UNIT = TupleT(())  # tipo de las funciones sin valor de retorno: ()




def is_copy(t: Type) -> bool:
    """Regla única de copia (decisión G1).

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
