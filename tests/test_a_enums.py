"""Enums: declaración, Enum::Variante, tag y payload."""

from rustiq.errors import E_ARG_COUNT, E_REDECLARED, E_TYPE_MISMATCH, E_UNKNOWN_TYPE, E_UNKNOWN_VARIANT
from tests.support import compile_wasm, compile_wat, error_codes, run

FORMA = "enum Forma { Punto, Cuadrado(i32), Rectangulo(i32, i32) }\n"


def test_variante_unitaria_guarda_su_tag():
    wat = compile_wat(FORMA + "fn crear() -> Forma { Forma::Punto }\nfn main() {}")
    assert "i32.const 0\n" in wat and "i32.store offset=0" in wat


def test_payload_va_desde_la_segunda_ranura():
    wat = compile_wat(FORMA + "fn crear() -> Forma { Forma::Rectangulo(3, 9) }\nfn main() {}")
    assert "i32.const 2\n" in wat  # tag de Rectangulo
    assert "i32.store offset=8" in wat and "i32.store offset=16" in wat
    assert "i32.const 24" in wat  # tag + 2 datos = 3 ranuras


def test_payload_f64_y_bool():
    src = "enum Dato { Num(f64), Flag(bool) }\nfn a() -> Dato { Dato::Num(2.5) }\nfn b() -> Dato { Dato::Flag(true) }\nfn main() {}"
    wat = compile_wat(src)
    assert "f64.store offset=8" in wat
    compile_wasm(src)


def test_enum_se_pasa_se_devuelve_y_se_anida():
    src = FORMA + """
enum Caja { Vacia, Con(Forma) }
struct Figura { forma: Forma, lado: i32 }
fn crear(l: i32) -> Forma { Forma::Cuadrado(l) }
fn guardar(f: Forma) -> Caja { Caja::Con(f) }
fn main() {
    let c = guardar(crear(7));
    let fig = Figura { forma: Forma::Punto, lado: 2 };
    print_i32(fig.lado);
}
"""
    assert run(src) == ["2"]


def test_enum_declarado_despues_de_su_uso():
    assert run("fn main() { let f = Forma::Punto; print_i32(1); }\n" + FORMA) == ["1"]


def test_enum_recursivo():
    src = "enum Lista { Nada, Cons(i32, Lista) }\nfn main() { let l = Lista::Cons(1, Lista::Cons(2, Lista::Nada)); print_i32(1); }"
    assert run(src) == ["1"]


# --- Inválidos -----------------------------------------------------------------


def test_enum_inexistente():
    assert error_codes("fn main() {\n    let f = Nada::Punto;\n}") == [(E_UNKNOWN_TYPE, 2, 13)]


def test_variante_inexistente():
    assert error_codes(FORMA + "fn main() {\n    let f = Forma::Circulo;\n}") == [(E_UNKNOWN_VARIANT, 3, 20)]


def test_datos_de_mas():
    assert error_codes(FORMA + "fn main() {\n    let f = Forma::Cuadrado(1, 2);\n}") == [(E_ARG_COUNT, 3, 13)]


def test_datos_de_menos():
    assert error_codes(FORMA + "fn main() {\n    let f = Forma::Rectangulo(1);\n}") == [(E_ARG_COUNT, 3, 13)]


def test_variante_con_datos_sin_parentesis():
    assert error_codes(FORMA + "fn main() {\n    let f = Forma::Cuadrado;\n}") == [(E_ARG_COUNT, 3, 13)]


def test_dato_de_otro_tipo():
    assert error_codes(FORMA + "fn main() {\n    let f = Forma::Cuadrado(true);\n}") == [(E_TYPE_MISMATCH, 3, 29)]


def test_variante_repetida_en_la_declaracion():
    assert error_codes("enum E { A, A }\nfn main() {}") == [(E_REDECLARED, 1, 13)]
