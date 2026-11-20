"""Generación de código de llamadas a funciones.

Dueño: A (Yerald). Lee `SemanticInfo` y nunca vuelve a inferir tipos.
"""

from rustiq.generated.RustiQParser import RustiQParser


class ItemsGenMixin:
    def gen_call(self, callee: RustiQParser.IdentPContext, call: RustiQParser.CallSuffixContext) -> None:
        """`nombre(args)`: apila los argumentos en orden y llama. El resultado queda en la pila."""
        if call.argumentList() is not None:
            for arg in call.argumentList().expression():
                self.visit(arg)
        self.emit(f"call ${callee.IDENT().getText()}")
