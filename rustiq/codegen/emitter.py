"""Base del generador de WAT.

Hereda un mixin por archivo. Cada mixin implementa solo los `visitX` de sus
reglas. Esta clase aporta lo común: el módulo, las líneas de salida y los
imports del host (ABI en docs/memoria.md).
"""

from rustiq.codegen.gen_arrays import ArraysGenMixin
from rustiq.codegen.gen_control import ControlGenMixin
from rustiq.codegen.gen_exprs import ExprsGenMixin
from rustiq.codegen.gen_match import MatchGenMixin
from rustiq.codegen.gen_refs import RefsGenMixin
from rustiq.codegen.gen_structs import StructsGenMixin
from rustiq.generated.RustiQVisitor import RustiQVisitor
from rustiq.semantic.info import SemanticInfo

INDENT = "  "

# (nombre, tipo Wasm del parámetro). Pendiente de aprobación del profesor (P1).
HOST_IMPORTS = (
    ("print_i32", "i32"),
    ("print_f64", "f64"),
    ("print_bool", "i32"),
    ("print_char", "i32"),
    ("print_str", "i32"),
)


class Emitter(
    ControlGenMixin, StructsGenMixin, MatchGenMixin,  # A
    ExprsGenMixin, ArraysGenMixin, RefsGenMixin,  # B
    RustiQVisitor,
):
    def __init__(self, info: SemanticInfo) -> None:
        self.info = info
        self._lines: list[str] = []
        self._depth = 0

    def emit(self, line: str = "") -> None:
        self._lines.append(INDENT * self._depth + line)

    def generate(self, tree) -> str:
        """Devuelve el módulo WAT completo."""
        self._lines = []
        self._depth = 0
        self.emit("(module")
        self._depth += 1
        for name, wasm_type in HOST_IMPORTS:
            self.emit(f'(import "env" "{name}" (func ${name} (param {wasm_type})))')
        self.emit('(memory (export "memory") 1)')
        self.visit(tree)  # TODO(A): runtime.wat, funciones y export de main
        self._depth -= 1
        self.emit(")")
        return "\n".join(self._lines) + "\n"
