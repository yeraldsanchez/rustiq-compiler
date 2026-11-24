"""pipeline.py: parse, semántica, codegen, wat2wasm y wasm-validate."""

from pathlib import Path

import pytest

from rustiq import pipeline
from tests.support import necesita_expresiones
from rustiq.errors import (
    BACKEND,
    E_INTERNAL,
    E_INVALID_CHAR,
    E_SYNTAX,
    E_WASM_INVALID,
    E_WAT_INVALID,
    LEXICO,
    SEMANTICO,
    SINTACTICO,
)

VALID_DIR = Path(__file__).parent / "valid"
WASM_MAGIC = b"\0asm"
WAT_ROTO = "(module (fnc))"
WASM_ROTO = WASM_MAGIC + b"\x01\0\0\0\xff"


def _sin_wabt(monkeypatch):
    """Simula una máquina sin wabt para forzar el respaldo de wasmtime."""
    monkeypatch.setattr(pipeline.shutil, "which", lambda _: None)


# --- compile_source ---------------------------------------------------------


@necesita_expresiones
@pytest.mark.parametrize("rq", sorted(VALID_DIR.glob("*.rq")), ids=lambda p: p.stem)
def test_programa_valido_produce_wasm(rq):
    result = pipeline.compile_source(rq.read_text(encoding="utf-8"))
    assert result.ok, result.errors
    assert result.errors == []
    assert result.wasm.startswith(WASM_MAGIC)
    assert "$alloc" in result.wat  # el runtime va dentro del módulo


def test_error_sintactico_con_posicion():
    result = pipeline.compile_source("fn main() {\n    let x = ;\n}\n")
    assert not result.ok
    assert (result.wat, result.wasm) == (None, None)
    e = result.errors[0]
    assert (e.phase, e.code, e.line, e.column) == (SINTACTICO, E_SYNTAX, 2, 13)


def test_error_lexico_con_posicion():
    result = pipeline.compile_source("fn main() {\n  @\n}\n")
    assert not result.ok
    assert result.wasm is None
    e = result.errors[0]
    assert (e.phase, e.code, e.line, e.column) == (LEXICO, E_INVALID_CHAR, 2, 3)


def test_errores_ordenados_por_posicion():
    _, errors = pipeline.parse_source("fn main() {\n  let = 1;\n  @\n}\n")
    posiciones = [(e.line, e.column) for e in errors]
    assert posiciones == sorted(posiciones)
    assert len(errors) >= 2


def test_parse_no_imprime_en_consola(capsys):
    pipeline.parse_source("fn main( {")
    assert capsys.readouterr().err == ""


def test_error_semantico_detiene_el_pipeline(monkeypatch):
    def analyze(self, tree):
        self.error(tree, "E_UNDECLARED", "prueba")
        return self.info, self.errors

    monkeypatch.setattr(pipeline.Analyzer, "analyze", analyze)
    result = pipeline.compile_source("fn main() {}")
    assert not result.ok
    assert (result.wat, result.wasm) == (None, None)
    assert result.errors[0].phase == SEMANTICO


def test_bug_del_analizador_es_error_interno(monkeypatch, caplog):
    def analyze(self, tree):
        raise RuntimeError("boom")

    monkeypatch.setattr(pipeline.Analyzer, "analyze", analyze)
    result = pipeline.compile_source("fn main() {}")
    e = result.errors[0]
    assert (e.phase, e.code) == (SEMANTICO, E_INTERNAL)
    # El detalle va al log, no al usuario.
    assert "boom" not in e.message
    assert "boom" in caplog.text


def test_bug_del_codegen_es_error_interno(monkeypatch):
    def generate(self, tree):
        raise RuntimeError("boom")

    monkeypatch.setattr(pipeline.Emitter, "generate", generate)
    result = pipeline.compile_source("fn main() {}")
    assert result.wasm is None
    assert (result.errors[0].phase, result.errors[0].code) == (BACKEND, E_INTERNAL)


def test_wat_invalido_del_codegen_no_devuelve_wasm(monkeypatch):
    monkeypatch.setattr(pipeline.Emitter, "generate", lambda self, tree: WAT_ROTO)
    result = pipeline.compile_source("fn main() {}")
    assert not result.ok
    assert (result.wat, result.wasm) == (None, None)
    e = result.errors[0]
    assert (e.phase, e.code, e.line, e.column) == (BACKEND, E_WAT_INVALID, 1, 1)


# --- Backend: wabt y respaldo con wasmtime -----------------------------------


def test_assemble_con_wabt():
    assert pipeline.assemble("(module)").startswith(WASM_MAGIC)


def test_assemble_sin_wabt(monkeypatch):
    _sin_wabt(monkeypatch)
    assert pipeline.assemble("(module)").startswith(WASM_MAGIC)


@pytest.mark.parametrize("con_wabt", [True, False], ids=["wabt", "wasmtime"])
def test_wat_invalido(monkeypatch, con_wabt):
    if not con_wabt:
        _sin_wabt(monkeypatch)
    with pytest.raises(pipeline.BackendError) as exc:
        pipeline.wat_to_wasm(WAT_ROTO)
    assert exc.value.error.code == E_WAT_INVALID


@pytest.mark.parametrize("con_wabt", [True, False], ids=["wabt", "wasmtime"])
def test_wasm_invalido(monkeypatch, con_wabt):
    if not con_wabt:
        _sin_wabt(monkeypatch)
    with pytest.raises(pipeline.BackendError) as exc:
        pipeline.validate_wasm(WASM_ROTO)
    assert exc.value.error.code == E_WASM_INVALID
