"""Generación de código de llamadas a funciones.

Dueño: A (Yerald). Lee `SemanticInfo` y nunca vuelve a inferir tipos.
"""

from rustiq.builtins import HOST_FUNCTIONS
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.tree import call_args

USER_FN_PREFIX = "$f_"  # evita choques con las funciones del runtime ($alloc, $memcpy...)
HOST_NAMES = {name for name, _ in HOST_FUNCTIONS}


def function_name(name: str) -> str:
    """Nombre Wasm de una función: las del host van tal cual, las del usuario con prefijo."""
    return f"${name}" if name in HOST_NAMES else f"{USER_FN_PREFIX}{name}"


class ItemsGenMixin:
    def gen_call(self, callee: RustiQParser.IdentPContext, call: RustiQParser.CallSuffixContext) -> None:
        """`nombre(args)`: apila los argumentos en orden y llama. El resultado queda en la pila."""
        for arg in call_args(call):
            self.visit(arg)
        self.emit(f"call {function_name(callee.IDENT().getText())}")
