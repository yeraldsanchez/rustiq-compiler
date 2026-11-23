"""Generación de código de referencias y Strings.

Dueño: B (Byron). Implementa solo los `visitX` de sus reglas. Lee `SemanticInfo` y
nunca vuelve a inferir tipos.
"""

from rustiq.generated.RustiQParser import RustiQParser as P


# Secuencias de escape de un literal (fragmento ESC de la gramática).
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}

# Los literales viven desde la dirección 0. El heap empieza después de ellos
# (en 1024 o más allá si no caben; ver Emitter._heap_start).


def unescape(raw_literal: str) -> str:
    """Texto de un literal sin comillas y con los escapes resueltos."""
    inner, out, i = raw_literal[1:-1], [], 0
    while i < len(inner):
        if inner[i] == "\\":
            out.append(ESCAPES[inner[i + 1]])
            i += 2
        else:
            out.append(inner[i])
            i += 1
    return "".join(out)


class RefsGenMixin:
    def emit_string_literal(self, raw_literal: str) -> None:
        data = unescape(raw_literal).encode("utf-8")
        offset = self._data_offset
        self._data_offset = offset + len(data)
        self._data_segments.append((offset, data))

        self.emit(f"i32.const {offset}")
        self.emit(f"i32.const {len(data)}")
        self.emit("call $str_new")

    def visitLiteralP(self, ctx: P.LiteralPContext):
        lit = ctx.literal()
        if lit is not None and lit.STRING_LIT() is not None:
            self.emit_string_literal(lit.STRING_LIT().getText())
        else:
            self.visit(lit)
