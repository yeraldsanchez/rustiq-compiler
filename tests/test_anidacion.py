"""Programas muy anidados: el compilador no debe caerse con RecursionError."""

from rustiq.host import run_wasm
from rustiq.pipeline import compile_source

PROFUNDIDAD = 1000


def test_parentesis_muy_anidados_compilan():
    expr = "(" * PROFUNDIDAD + "7" + ")" * PROFUNDIDAD
    result = compile_source(f"fn main() {{ print_i32({expr}); }}")
    assert result.ok, result.errors
    assert run_wasm(result.wasm) == "7\n"


def test_if_muy_anidados_compilan():
    cuerpo = "if true { " * 300 + "print_i32(5);" + " }" * 300
    result = compile_source(f"fn main() {{ {cuerpo} }}")
    assert result.ok, result.errors
    assert run_wasm(result.wasm) == "5\n"


def test_error_dentro_de_anidacion_se_reporta():
    expr = "(" * 500 + "true" + ")" * 500
    result = compile_source(f"fn main() {{ print_i32({expr}); }}")
    assert not result.ok
    assert result.errors[0].code == "E_TYPE_MISMATCH"
