"""Match: patrones, mismo tipo en todos los brazos, exhaustividad y codegen."""

from rustiq.errors import E_BAD_PATTERN, E_NOT_EXHAUSTIVE, E_TYPE_MISMATCH, E_UNDECLARED
from tests.support import error_codes, run


def _imprime(funcion: str, llamadas: list[str]) -> str:
    cuerpo = " ".join(f"print_i32({c});" for c in llamadas)
    return funcion + f"\nfn main() {{ {cuerpo} }}"


# --- Literales, _ e identificadores --------------------------------------------


def test_literales_enteros_con_comodin():
    f = "fn dia(d: i32) -> i32 { match d { 1 => 100, 2 => 200, _ => 0 } }"
    assert run(_imprime(f, ["dia(1)", "dia(2)", "dia(9)"])) == ["100", "200", "0"]


def test_brazo_identificador_liga_el_valor():
    f = "fn doble(n: i32) -> i32 { match n { 0 => -1, x => x * 2 } }"
    assert run(_imprime(f, ["doble(0)", "doble(21)"])) == ["-1", "42"]


def test_bool_con_true_y_false_es_exhaustivo():
    f = "fn a_num(b: bool) -> i32 { match b { true => 1, false => 0 } }"
    assert run(_imprime(f, ["a_num(true)", "a_num(false)"])) == ["1", "0"]


def test_match_sobre_char_y_f64():
    src = """
fn vocal(c: char) -> bool { match c { 'a' => true, 'e' => true, _ => false } }
fn mitad(x: f64) -> f64 { match x { 0.0 => 0.0, v => v / 2.0 } }
fn main() { print_bool(vocal('e')); print_bool(vocal('z')); print_f64(mitad(5.0)); }
"""
    assert run(src) == ["true", "false", "2.5"]


def test_resultado_en_let_y_como_argumento():
    src = """
fn main() {
    let n = 3;
    let r = match n { 3 => 30, _ => 0 };
    print_i32(r);
    print_i32(match n { 1 => 1, _ => 99 } + 1);
}
"""
    assert run(src) == ["30", "100"]


def test_match_como_sentencia_con_brazos_unit():
    src = """
fn main() {
    let n = 2;
    match n { 1 => print_i32(10), _ => print_i32(20) };
    print_i32(n);
}
"""
    assert run(src) == ["20", "2"]


def test_match_anidado_en_un_brazo():
    f = "fn f(a: i32, b: i32) -> i32 { match a { 0 => match b { 0 => 1, _ => 2 }, _ => 3 } }"
    assert run(_imprime(f, ["f(0, 0)", "f(0, 5)", "f(1, 0)"])) == ["1", "2", "3"]


def test_brazo_con_return_y_break_dentro_de_un_ciclo():
    src = """
fn main() {
    let mut i = 0;
    loop {
        match i { 3 => { break; }, _ => { print_i32(i); } };
        i = i + 1;
    }
}
"""
    assert run(src) == ["0", "1", "2"]


def test_mismo_binding_en_dos_brazos_no_choca():
    f = "fn f(n: i32) -> i32 { match n { 0 => 0, x => x } }\nfn g(n: i32) -> i32 { match n { x => x + 1 } }"
    assert run(_imprime(f, ["f(4)", "g(4)"])) == ["4", "5"]


# --- Inválidos -----------------------------------------------------------------


def test_enteros_sin_comodin_no_es_exhaustivo():
    src = "fn f(n: i32) -> i32 {\n    match n { 1 => 1, 2 => 2 }\n}\nfn main() {}"
    assert error_codes(src) == [(E_NOT_EXHAUSTIVE, 2, 5)]


def test_bool_con_solo_true_no_es_exhaustivo():
    src = "fn f(b: bool) -> i32 {\n    match b { true => 1 }\n}\nfn main() {}"
    assert error_codes(src) == [(E_NOT_EXHAUSTIVE, 2, 5)]


def test_brazos_con_tipos_distintos():
    src = "fn f(n: i32) -> i32 {\n    match n { 1 => 1, _ => true }\n}\nfn main() {}"
    assert error_codes(src) == [(E_TYPE_MISMATCH, 2, 28)]


def test_literal_de_otro_tipo_en_patron():
    src = "fn f(n: i32) -> i32 {\n    match n { true => 1, _ => 0 }\n}\nfn main() {}"
    assert error_codes(src) == [(E_TYPE_MISMATCH, 2, 15)]


def test_literal_string_en_patron():
    src = 'fn f(n: i32) -> i32 {\n    match n { "a" => 1, _ => 0 }\n}\nfn main() {}'
    assert error_codes(src) == [(E_BAD_PATTERN, 2, 15)]


def test_binding_no_existe_fuera_de_su_brazo():
    src = "fn f(n: i32) -> i32 {\n    let r = match n { x => x };\n    x\n}\nfn main() {}"
    assert error_codes(src) == [(E_UNDECLARED, 3, 5)]


def test_brazo_con_patron_erroneo_no_genera_errores_en_cascada():
    src = 'fn f(n: i32) -> i32 {\n    match n { "a" => y, _ => 0 }\n}\nfn main() {}'
    assert error_codes(src) == [(E_BAD_PATTERN, 2, 15)]


def test_match_con_valor_erroneo_no_revisa_los_brazos():
    src = "fn f() -> i32 {\n    match nada { 1 => 1 }\n}\nfn main() {}"
    assert error_codes(src) == [(E_UNDECLARED, 2, 11)]



# --- Tuplas --------------------------------------------------------------------


def test_tupla_de_identificadores_es_exhaustiva():
    f = "fn suma(p: (i32, i32)) -> i32 { match p { (a, b) => a + b } }"
    assert run(_imprime(f, ["suma((3, 8))"])) == ["11"]


def test_tupla_como_resultado_del_match():
    src = """
fn intercambiar(p: (i32, i32)) -> (i32, i32) { match p { (a, b) => (b, a) } }
fn primero(p: (i32, i32)) -> i32 { match p { (a, _) => a } }
fn main() { print_i32(primero(intercambiar((3, 8)))); }
"""
    assert run(src) == ["8"]


def test_tupla_con_literales_y_comodines():
    src = """
fn clase(p: (i32, bool)) -> i32 { match p { (11, true) => 1, (_, false) => 2, _ => 3 } }
fn main() { print_i32(clase((11, true))); print_i32(clase((5, false))); print_i32(clase((5, true))); }
"""
    assert run(src) == ["1", "2", "3"]


def test_tupla_anidada_y_con_f64():
    src = """
fn f(p: ((i32, f64), bool)) -> f64 { match p { ((1, x), true) => x, ((_, y), _) => y * 2.0 } }
fn main() { print_f64(f(((1, 1.5), true))); print_f64(f(((2, 1.5), true))); }
"""
    assert run(src) == ["1.5", "3.0"]


def test_patron_de_tupla_sobre_entero():
    src = "fn f(n: i32) -> i32 {\n    match n { (a, b) => a }\n}\nfn main() {}"
    assert error_codes(src) == [(E_BAD_PATTERN, 2, 15)]


def test_tupla_de_otra_aridad():
    src = "fn f(p: (i32, i32)) -> i32 {\n    match p { (a, b, c) => a }\n}\nfn main() {}"
    assert error_codes(src) == [(E_TYPE_MISMATCH, 2, 15)]


def test_tupla_con_literal_sin_comodin_no_es_exhaustiva():
    src = "fn f(p: (i32, i32)) -> i32 {\n    match p { (1, x) => x }\n}\nfn main() {}"
    assert error_codes(src) == [(E_NOT_EXHAUSTIVE, 2, 5)]
