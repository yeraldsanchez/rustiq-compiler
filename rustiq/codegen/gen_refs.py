"""Generación de código de referencias y Strings.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos.
"""

from rustiq.generated.RustiQParser import RustiQParser


class RefsGenMixin:
    def _string_segments(self) -> list[tuple[int, bytes]]:
        return self.__dict__.setdefault("_data_segments", [])

    def emit_string_literal(self, raw_literal: str) -> None:
        inner = raw_literal[1:-1]
        data = inner.encode("utf-8")
        offset = self.__dict__.get("_data_offset", 0)
        self._data_offset = offset + len(data)
        self._string_segments().append((offset, data))

        self.emit(f"i32.const {offset}")
        self.emit(f"i32.const {len(data)}")
        self.emit("call $str_new")

    def visitLiteralP(self, ctx: RustiQParser.LiteralPContext):
        lit = ctx.literal()
        if lit is not None and lit.STRING_LIT() is not None:
            self.emit_string_literal(lit.STRING_LIT().getText())
        else:
            self.visit(lit)
