"""Implementación por defecto del contrato de ámbitos.

La tabla de símbolos real es de B (Byron) en `scopes.py`. Esta clase va al final
de la herencia del Analyzer, así que `ScopesMixin` la reemplaza en cuanto defina
los mismos métodos. Mientras tanto permite que el carril A funcione y se pruebe.

Contrato que usa el carril A:
    push_scope() / pop_scope()
    declare(name, type, mutable, kind, node) -> Symbol | None   (None si ya existía)
    lookup(name) -> Symbol | None
"""

from rustiq.errors import E_REDECLARED
from rustiq.semantic.info import Symbol
from rustiq.types import Type


class ScopeDefaults:
    def push_scope(self) -> None:
        self.__dict__.setdefault("_scopes", []).append({})

    def pop_scope(self) -> None:
        self._scopes.pop()

    def declare(self, name: str, type: Type, mutable: bool, kind: str, node) -> Symbol | None:
        scope = self._scopes[-1]
        if name in scope:
            self.error(node, E_REDECLARED, f"'{name}' ya fue declarado en este ámbito")
            return None
        uid = self.__dict__.get("_next_uid", 0)
        self._next_uid = uid + 1
        symbol = Symbol(uid, name, type, mutable, kind)
        scope[name] = symbol
        return symbol

    def lookup(self, name: str) -> Symbol | None:
        for scope in reversed(self.__dict__.get("_scopes", [])):
            if name in scope:
                return scope[name]
        return None
