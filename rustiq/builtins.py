"""Funciones que el host importa desde `env` (ABI en docs/memoria.md).

Son la única fuente de verdad: el análisis las registra como funciones
normales y el emisor las declara como imports.
"""

from rustiq.types import BOOL, CHAR, F64, I32, STRING, Type

# (nombre, tipo del único parámetro). Todas devuelven ().
HOST_FUNCTIONS: tuple[tuple[str, Type], ...] = (
    ("print_i32", I32),
    ("print_f64", F64),
    ("print_bool", BOOL),
    ("print_char", CHAR),
    ("print_str", STRING),
)
