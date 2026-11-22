"""Movimientos: estados, uso después de mover, ramas y ciclos (G1, G8, T4)."""

from rustiq.errors import E_MOVE_WHILE_BORROWED, E_UNINITIALIZED, E_USE_AFTER_MOVE
from rustiq.pipeline import compile_source
from tests.support import error_codes

PUNTO = "struct Punto { x: i32, y: i32 }\nfn usar(p: Punto) {}\nfn nada() {}\n"

def errores_reales(source: str) -> list[tuple[str, int, int]]:
    return [(e.code, e.line, e.column) for e in compile_source(source).errors]


# --- Ciclos (funciona sin B) ---------------------------------------------------


def test_mover_un_parametro_dentro_de_un_ciclo():
    src = PUNTO + "fn f(p: Punto) {\n    loop {\n        usar(p);\n        break;\n    }\n}\nfn main() {}"
    assert error_codes(src) == [(E_USE_AFTER_MOVE, 6, 14)]


def test_mover_dentro_de_while_al_construir_una_tupla():
    src = PUNTO + "fn f(p: Punto, c: bool) {\n    while c {\n        let t = (p, 1);\n    }\n}\nfn main() {}"
    assert error_codes(src) == [(E_USE_AFTER_MOVE, 6, 18)]


def test_un_valor_copy_no_se_mueve_en_un_ciclo():
    src = "fn g(n: i32) {}\nfn f(n: i32) {\n    loop {\n        g(n);\n        break;\n    }\n}\nfn main() {}"
    assert error_codes(src) == []


def test_leer_un_campo_no_mueve():
    src = PUNTO + "fn g(n: i32) {}\nfn f(p: Punto) {\n    loop {\n        g(p.x);\n        break;\n    }\n}\nfn main() {}"
    assert error_codes(src) == []


def test_binding_declarado_dentro_del_ciclo_se_puede_mover():
    src = PUNTO + """
enum Caja { Con(Punto) }
fn f(c: bool) {
    while c {
        match Caja::Con((Punto { x: 1, y: 2 })) { Caja::Con(p) => usar(p) };
    }
}
fn main() {}
"""
    assert error_codes(src) == []


def test_match_sobre_un_parametro_sin_bindings_no_lo_mueve():
    src = "enum Luz { Roja, Verde }\nfn nada() {}\nfn f(l: Luz) {\n    loop {\n        match l { Luz::Roja => nada(), _ => nada() };\n        break;\n    }\n}\nfn main() {}"
    assert error_codes(src) == []


def test_match_que_liga_un_valor_no_copy_mueve_su_valor():
    src = PUNTO + "enum Caja { Con(Punto) }\nfn f(c: Caja) {\n    loop {\n        match c { Caja::Con(p) => usar(p) };\n        break;\n    }\n}\nfn main() {}"
    assert error_codes(src) == [(E_USE_AFTER_MOVE, 7, 15)]


# --- Uso después de mover (necesita B) ----------------------------------------


def test_uso_despues_de_mover_con_let():
    src = PUNTO + "fn main() {\n    let a = Punto { x: 1, y: 2 };\n    let b = a;\n    usar(a);\n}"
    assert errores_reales(src) == [(E_USE_AFTER_MOVE, 7, 10)]


def test_uso_despues_de_pasar_a_una_funcion():
    src = PUNTO + "fn main() {\n    let a = Punto { x: 1, y: 2 };\n    usar(a);\n    usar(a);\n}"
    assert errores_reales(src) == [(E_USE_AFTER_MOVE, 7, 10)]


def test_reinicializar_despues_de_mover_es_valido():
    src = PUNTO + "fn main() {\n    let mut a = Punto { x: 1, y: 2 };\n    usar(a);\n    a = Punto { x: 3, y: 4 };\n    usar(a);\n}"
    assert errores_reales(src) == []


def test_movido_en_una_rama_queda_movido_despues_del_if():
    src = PUNTO + "fn main() {\n    let c = true;\n    let a = Punto { x: 1, y: 2 };\n    if c { usar(a); }\n    usar(a);\n}"
    assert errores_reales(src) == [(E_USE_AFTER_MOVE, 8, 10)]


def test_reponer_dentro_de_la_rama_no_cuenta():
    src = PUNTO + "fn main() {\n    let c = true;\n    let mut a = Punto { x: 1, y: 2 };\n    if c { usar(a); a = Punto { x: 0, y: 0 }; }\n    usar(a);\n}"
    assert errores_reales(src) == [(E_USE_AFTER_MOVE, 8, 10)]


def test_cada_rama_empieza_con_el_estado_de_antes():
    src = PUNTO + "fn main() {\n    let c = true;\n    let a = Punto { x: 1, y: 2 };\n    if c { usar(a); } else { usar(a); }\n}"
    assert errores_reales(src) == []


def test_uso_antes_de_asignar():
    src = PUNTO + "fn main() {\n    let a: Punto;\n    usar(a);\n}"
    assert errores_reales(src) == [(E_UNINITIALIZED, 6, 10)]


def test_mover_un_valor_prestado():
    src = PUNTO + "fn main() {\n    let a = Punto { x: 1, y: 2 };\n    let r = &a;\n    usar(a);\n}"
    assert errores_reales(src) == [(E_MOVE_WHILE_BORROWED, 7, 10)]
