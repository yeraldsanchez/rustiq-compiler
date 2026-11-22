"""Operadores unarios y binarios, con el pipeline real."""

from rustiq.errors import E_BAD_OPERAND, E_TYPE_MISMATCH
from rustiq.host import run_wasm
from rustiq.pipeline import compile_source


def errores(source: str) -> list[tuple[str, int, int]]:
    return [(e.code, e.line, e.column) for e in compile_source(source).errors]


def salida(cuerpo: str, extra: str = "") -> str:
    result = compile_source(extra + "fn main() {\n" + cuerpo + "\n}")
    assert result.ok, result.errors
    return run_wasm(result.wasm)


# --- Ejecución -----------------------------------------------------------------


def test_aritmetica_i32_con_precedencia_y_parentesis():
    assert salida("print_i32(2 + 3 * 4);\nprint_i32((2 + 3) * 4);\nprint_i32(17 % 5);\nprint_i32(7 / 2 - 10);") == "14\n20\n2\n-7\n"


def test_aritmetica_f64():
    assert salida("print_f64(1.5 * 2.0 + 0.25);\nprint_f64(1.0 / 4.0);") == "3.25\n0.25\n"


def test_unarios():
    assert salida("let x = 5;\nprint_i32(-x);\nprint_f64(-2.5);\nprint_bool(!true);") == "-5\n-2.5\nfalse\n"


def test_comparaciones():
    src = "print_bool(3 < 4);\nprint_bool(2.5 >= 3.0);\nprint_bool('a' == 'a');\nprint_bool(true != false);"
    assert salida(src) == "true\nfalse\ntrue\ntrue\n"


def test_and_y_or():
    src = "print_bool(true && false);\nprint_bool(false || true);\nprint_bool(1 < 2 && 2 < 3 && 3 < 1);"
    assert salida(src) == "false\ntrue\nfalse\n"


def test_cortocircuito_no_evalua_el_lado_derecho():
    extra = "fn ruido() -> bool {\n    print_i32(99);\n    true\n}\n"
    assert salida("print_bool(false && ruido());\nprint_bool(true || ruido());", extra) == "false\ntrue\n"


def test_cortocircuito_si_evalua_cuando_hace_falta():
    extra = "fn ruido() -> bool {\n    print_i32(99);\n    true\n}\n"
    assert salida("print_bool(true && ruido());", extra) == "99\ntrue\n"


def test_referencia_a_struct_es_el_mismo_puntero():
    extra = "struct Punto { x: i32, y: i32 }\nfn suma(p: &Punto) -> i32 { p.x + p.y }\n"
    assert salida("let p = Punto { x: 2, y: 3 };\nprint_i32(suma(&p));", extra) == "5\n"


# --- Errores -------------------------------------------------------------------


def test_resto_de_f64_no_existe():
    assert errores("fn main() {\n    let x = 5.0 % 2.0;\n}") == [(E_BAD_OPERAND, 2, 13)]


def test_operandos_de_tipos_distintos():
    assert errores("fn main() {\n    let x = 1 + 2.0;\n}") == [(E_TYPE_MISMATCH, 2, 17)]


def test_and_con_enteros():
    assert errores("fn main() {\n    let x = 1 && 2;\n}") == [(E_BAD_OPERAND, 2, 13)]


def test_menor_que_con_bool():
    assert errores("fn main() {\n    let x = true < false;\n}") == [(E_BAD_OPERAND, 2, 13)]


def test_not_de_un_entero():
    assert errores("fn main() {\n    let x = !1;\n}") == [(E_BAD_OPERAND, 2, 13)]


def test_menos_de_un_bool():
    assert errores("fn main() {\n    let x = -true;\n}") == [(E_BAD_OPERAND, 2, 13)]


def test_desreferenciar_algo_que_no_es_referencia():
    assert errores("fn main() {\n    let x = 1;\n    let y = *x;\n}") == [(E_BAD_OPERAND, 3, 13)]


def test_condicion_con_comparacion_es_bool():
    assert errores("fn main() {\n    let x = 1;\n    if x < 2 {\n        print_i32(x);\n    }\n}") == []
