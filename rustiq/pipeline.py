"""Pipeline completo: parse, semántica, codegen, wat2wasm y wasm-validate.

Dueño: A (Yerald). Por ahora solo define la interfaz que usa el runner de
pruebas y el servidor; la implementación llega en la Etapa 1.
"""

from dataclasses import dataclass, field

from rustiq.errors import CompileError


@dataclass
class CompileResult:
    ok: bool
    errors: list[CompileError] = field(default_factory=list)
    wat: str | None = None
    wasm: bytes | None = None


def compile_source(source: str) -> CompileResult:
    """Compila un programa RustiQ. Si hay un solo error, no devuelve wasm."""
    raise NotImplementedError("pipeline pendiente (Etapa 1)")
