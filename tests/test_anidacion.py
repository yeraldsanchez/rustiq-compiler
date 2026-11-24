"""Programas muy anidados: el compilador no debe caerse con RecursionError,
y pasado MAX_NESTING los rechaza con un error en vez de parsearlos."""

from rustiq.host import run_wasm
from rustiq.pipeline import MAX_NESTING, compile_source


def test_parentesis_muy_anidados_compilan():
    # print_i32( ya abre un nivel dentro de las llaves de main.
    profundidad = MAX_NESTING - 2
    expr = "(" * profundidad + "7" + ")" * profundidad
    result = compile_source(f"fn main() {{ print_i32({expr}); }}")
    assert result.ok, result.errors
    assert run_wasm(result.wasm) == "7\n"


def test_if_muy_anidados_compilan():
    # Las llaves de main y el paréntesis de print_i32 suman dos niveles.
    profundidad = MAX_NESTING - 2
    cuerpo = "if true { " * profundidad + "print_i32(5);" + " }" * profundidad
    result = compile_source(f"fn main() {{ {cuerpo} }}")
    assert result.ok, result.errors
    assert run_wasm(result.wasm) == "5\n"


def test_error_dentro_de_anidacion_se_reporta():
    expr = "(" * 200 + "true" + ")" * 200
    result = compile_source(f"fn main() {{ print_i32({expr}); }}")
    assert not result.ok
    assert result.errors[0].code == "E_TYPE_MISMATCH"


def test_anidacion_de_mas_se_rechaza():
    profundidad = MAX_NESTING
    expr = "(" * profundidad + "7" + ")" * profundidad
    result = compile_source(f"fn main() {{ print_i32({expr}); }}")
    assert not result.ok
    [error] = result.errors
    assert error.code == "E_TOO_NESTED"
    # Apunta al primer paréntesis que se pasa del límite.
    assert (error.line, error.column) == (1, len("fn main() { print_i32(") + MAX_NESTING - 1)


def test_bloques_sin_cerrar_de_mas_se_rechazan():
    result = compile_source("fn main() " + "{" * 50_000)
    assert [e.code for e in result.errors] == ["E_TOO_NESTED"]


def test_delimitadores_en_strings_y_comentarios_no_cuentan():
    relleno = "(" * (MAX_NESTING * 2)
    source = f'fn main() {{\n    // {relleno}\n    /* {relleno} */\n    print_str("{relleno}");\n}}\n'
    result = compile_source(source)
    assert result.ok, result.errors
