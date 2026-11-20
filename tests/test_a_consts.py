"""Constantes globales y locales."""

from rustiq.errors import E_REDECLARED, E_TYPE_MISMATCH
from tests.support import error_codes, run


def test_const_global_en_una_funcion():
    assert run("const LIMITE: i32 = 5;\nfn main() { print_i32(LIMITE * 2); }") == ["10"]


def test_const_global_declarada_despues_y_encadenada():
    src = """
fn main() { print_i32(B); }
const B: i32 = A + 1;
const A: i32 = 41;
"""
    assert run(src) == ["42"]


def test_const_local():
    assert run("fn main() { const K: i32 = 3; print_i32(K + K); }") == ["6"]


def test_const_global_visible_en_varias_funciones():
    src = "const N: i32 = 7;\nfn f() -> i32 { N }\nfn main() { print_i32(f() + N); }"
    assert run(src) == ["14"]


def test_const_f64():
    assert run("const PI: f64 = 3.5;\nfn main() { print_f64(PI); }") == ["3.5"]


def test_const_global_de_struct_se_crea_en_cada_uso():
    src = """
struct P { x: i32 }
const ORIGEN: P = P { x: 9 };
fn main() { print_i32(ORIGEN.x); print_i32(ORIGEN.x); }
"""
    assert run(src) == ["9", "9"]


# --- Inválidos -----------------------------------------------------------------


def test_const_global_con_tipo_incorrecto():
    assert error_codes("const A: i32 = true;\nfn main() {}") == [(E_TYPE_MISMATCH, 1, 16)]


def test_const_local_con_tipo_incorrecto():
    assert error_codes("fn main() {\n    const A: bool = 1;\n}") == [(E_TYPE_MISMATCH, 2, 21)]


def test_const_duplicada():
    assert error_codes("const A: i32 = 1;\nconst A: i32 = 2;\nfn main() {}") == [(E_REDECLARED, 2, 7)]


def test_const_local_duplicada_en_el_mismo_ambito():
    src = "fn main() {\n    const A: i32 = 1;\n    const A: i32 = 2;\n}"
    assert error_codes(src) == [(E_REDECLARED, 3, 11)]
