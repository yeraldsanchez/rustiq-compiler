"""Los esqueletos de Analyzer y Emitter ya ensamblan y corren sobre un programa real."""

import subprocess
from pathlib import Path

from antlr4 import CommonTokenStream, InputStream

from rustiq.codegen.emitter import Emitter
from rustiq.generated.RustiQLexer import RustiQLexer
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.analyzer import Analyzer
from rustiq.semantic.info import SemanticInfo
from tests.support import PROGRAMA_MINIMO

EJEMPLO = Path(__file__).parent / "valid" / "structs_basico.rq"


def _parse(source: str):
    parser = RustiQParser(CommonTokenStream(RustiQLexer(InputStream(source))))
    tree = parser.program()
    assert parser.getNumberOfSyntaxErrors() == 0
    return tree


def test_analyzer_corre_sin_errores():
    info, errors = Analyzer().analyze(_parse(EJEMPLO.read_text(encoding="utf-8")))
    assert errors == []
    assert isinstance(info, SemanticInfo)


def test_analyzer_error_con_posicion():
    tree = _parse("fn main() {}")
    analyzer = Analyzer()
    analyzer.error(tree.item(0), "E_INTERNAL", "prueba")
    e = analyzer.errors[0]
    assert (e.phase, e.code, e.line, e.column, e.length) == ("semantico", "E_INTERNAL", 1, 1, 12)


def test_emitter_genera_modulo_valido(tmp_path):
    tree = _parse(PROGRAMA_MINIMO)
    info, _ = Analyzer().analyze(tree)
    wat = Emitter(info).generate(tree)

    wat_file, wasm_file = tmp_path / "m.wat", tmp_path / "m.wasm"
    wat_file.write_text(wat)
    subprocess.run(["wat2wasm", str(wat_file), "-o", str(wasm_file)], check=True)
    subprocess.run(["wasm-validate", str(wasm_file)], check=True)
