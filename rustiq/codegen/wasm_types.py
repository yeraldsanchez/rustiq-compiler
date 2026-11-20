"""Tipos de Wasm de los valores de RustiQ (docs/memoria.md)."""

from rustiq.types import F64, Type


def wasm_type(t: Type) -> str:
    """f64 va en f64; todo lo demás (enteros, punteros, referencias) en i32."""
    return "f64" if t == F64 else "i32"
