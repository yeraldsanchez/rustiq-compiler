"""Control de flujo: if, while, loop, break, continue, return y bloques."""

from rustiq.errors import E_BREAK_OUTSIDE_LOOP, E_TYPE_MISMATCH
from tests.support import error_codes, run


def test_if_else():
    src = """
fn main() {
    if 1 < 2 { print_i32(1); } else { print_i32(2); }
    if 1 > 2 { print_i32(3); } else { print_i32(4); }
    if false { print_i32(5); }
}
"""
    assert run(src) == ["1", "4"]


def test_else_if_encadenado():
    src = """
fn clasificar(n: i32) -> i32 {
    if n < 0 { return 0 - 1; } else if n == 0 { return 0; } else { return 1; }
}
fn main() {
    print_i32(clasificar(0 - 8));
    print_i32(clasificar(0));
    print_i32(clasificar(42));
}
"""
    assert run(src) == ["-1", "0", "1"]


def test_while_con_continue():
    src = """
fn main() {
    let mut i = 0;
    let mut impares = 0;
    while i < 10 {
        i += 1;
        if i % 2 == 0 { continue; }
        impares += i;
    }
    print_i32(impares);
}
"""
    assert run(src) == ["25"]


def test_loop_con_break():
    src = """
fn main() {
    let mut k = 30;
    loop {
        k += 1;
        if k % 7 == 0 { break; }
    }
    print_i32(k);
}
"""
    assert run(src) == ["35"]


def test_ciclos_anidados_rompen_el_mas_interno():
    src = """
fn main() {
    let mut i = 0;
    while i < 3 {
        i += 1;
        let mut j = 0;
        loop {
            j += 1;
            if j == 2 { break; }
        }
        print_i32(i * 10 + j);
    }
}
"""
    assert run(src) == ["12", "22", "32"]


def test_return_dentro_de_un_loop():
    src = """
fn primero_mayor(n: i32) -> i32 {
    let mut i = 0;
    loop {
        i += 1;
        if i * i > n { return i; }
    }
}
fn main() { print_i32(primero_mayor(50)); }
"""
    assert run(src) == ["8"]


def test_bloque_con_valor_final():
    src = """
fn main() {
    let x = { let a = 2; a * 3 };
    print_i32(x);
}
"""
    assert run(src) == ["6"]


def test_bloque_como_sentencia_y_ambito():
    src = """
fn main() {
    let x = 1;
    { let x = 5; print_i32(x); }
    print_i32(x);
}
"""
    assert run(src) == ["5", "1"]


def test_return_en_funcion_unit():
    src = "fn f(n: i32) { if n > 0 { return; } print_i32(0); }\nfn main() { f(1); f(0); }"
    assert run(src) == ["0"]


# --- Inválidos -----------------------------------------------------------------


def test_condicion_no_bool():
    assert error_codes("fn main() {\n    if 1 { }\n}") == [(E_TYPE_MISMATCH, 2, 8)]
    assert error_codes("fn main() {\n    while 1 + 1 { }\n}") == [(E_TYPE_MISMATCH, 2, 11)]


def test_break_y_continue_fuera_de_ciclo():
    assert error_codes("fn main() {\n    break;\n}") == [(E_BREAK_OUTSIDE_LOOP, 2, 5)]
    assert error_codes("fn main() {\n    continue;\n}") == [(E_BREAK_OUTSIDE_LOOP, 2, 5)]


def test_break_dentro_de_if_sin_ciclo():
    assert error_codes("fn main() {\n    if true { break; }\n}")[0][0] == E_BREAK_OUTSIDE_LOOP


def test_if_no_produce_valor():
    # P4: if es solo sentencia, sus ramas no pueden devolver un valor
    src = "fn main() {\n    if true { 1 } else { 2 }\n}"
    assert [c for c, *_ in error_codes(src)] == [E_TYPE_MISMATCH, E_TYPE_MISMATCH]


def test_cuerpo_de_ciclo_no_produce_valor():
    assert error_codes("fn main() {\n    while false { 1 }\n}") == [(E_TYPE_MISMATCH, 2, 19)]
