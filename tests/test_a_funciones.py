"""Funciones y llamadas: firmas, argumentos, retorno y recursión."""

from rustiq.errors import (
    E_ARG_COUNT,
    E_BAD_MAIN,
    E_BAD_RETURN,
    E_NOT_CALLABLE,
    E_REDECLARED,
    E_TYPE_MISMATCH,
    E_UNDECLARED,
)
from tests.support import error_codes, run


def test_llamada_a_builtin():
    assert run("fn main() { print_i32(42); }") == ["42"]


def test_funcion_con_parametros_y_retorno():
    src = "fn suma(a: i32, b: i32) -> i32 { a + b }\nfn main() { print_i32(suma(2, 3)); }"
    assert run(src) == ["5"]


def test_recursion_y_return_anticipado():
    src = """
fn fact(n: i32) -> i32 {
    if n <= 1 { return 1; }
    n * fact(n - 1)
}
fn main() { print_i32(fact(5)); }
"""
    assert run(src) == ["120"]


def test_funcion_que_termina_en_return():
    src = "fn dos() -> i32 { return 2; }\nfn main() { print_i32(dos()); }"
    assert run(src) == ["2"]


def test_funciones_declaradas_despues_de_main():
    assert run("fn main() { print_i32(valor()); }\nfn valor() -> i32 { 7 }") == ["7"]


def test_f64_y_bool_y_char():
    src = """
fn mitad(x: f64) -> f64 { x / 2.0 }
fn main() { print_f64(mitad(5.0)); print_bool(true); print_char('R'); }
"""
    assert run(src) == ["2.5", "true", "R"]


def test_valor_descartado_en_sentencia():
    assert run("fn uno() -> i32 { 1 }\nfn main() { uno(); print_i32(2); }") == ["2"]


# --- Inválidos -----------------------------------------------------------------


def test_funcion_inexistente():
    assert error_codes("fn main() {\n    nada();\n}") == [(E_UNDECLARED, 2, 5)]


def test_llamar_algo_que_no_es_funcion():
    assert error_codes("fn main() {\n    let x = 1;\n    x();\n}") == [(E_NOT_CALLABLE, 3, 5)]


def test_pocos_argumentos():
    src = "fn f(a: i32, b: i32) {}\nfn main() {\n    f(1);\n}"
    assert error_codes(src) == [(E_ARG_COUNT, 3, 5)]


def test_demasiados_argumentos():
    assert error_codes("fn f() {}\nfn main() {\n    f(1);\n}") == [(E_ARG_COUNT, 3, 5)]


def test_tipo_de_argumento():
    src = "fn f(a: i32) {}\nfn main() {\n    f(true);\n}"
    assert error_codes(src) == [(E_TYPE_MISMATCH, 3, 7)]


def test_tipo_de_retorno_incorrecto():
    src = "fn f() -> i32 {\n    true\n}\nfn main() {}"
    assert error_codes(src) == [(E_BAD_RETURN, 2, 5)]


def test_retorno_faltante():
    src = "fn f() -> i32 {\n    let x = 1;\n}\nfn main() {}"
    assert error_codes(src) == [(E_BAD_RETURN, 3, 1)]


def test_return_con_valor_en_funcion_unit():
    assert error_codes("fn main() {\n    return 1;\n}") == [(E_BAD_RETURN, 2, 12)]


def test_return_sin_valor_en_funcion_con_tipo():
    src = "fn f() -> i32 {\n    return;\n}\nfn main() {}"
    assert error_codes(src) == [(E_BAD_RETURN, 2, 5)]


def test_return_de_otro_tipo():
    src = "fn f() -> i32 {\n    return true;\n}\nfn main() {}"
    assert error_codes(src) == [(E_BAD_RETURN, 2, 12)]


def test_funcion_duplicada():
    assert error_codes("fn f() {}\nfn f() {}\nfn main() {}") == [(E_REDECLARED, 2, 4)]


def test_sin_main():
    assert error_codes("fn f() {}")[0][0] == E_BAD_MAIN


def test_main_con_parametros_o_retorno():
    assert error_codes("fn main(a: i32) {}")[0][0] == E_BAD_MAIN
    assert error_codes("fn main() -> i32 { 1 }")[0][0] == E_BAD_MAIN


def test_no_se_puede_redefinir_un_builtin():
    assert error_codes("fn print_i32() {}\nfn main() {}")[0][0] == E_REDECLARED
