"""Préstamos: vida de `&` y `&mut` por sentencia y por ámbito."""

from rustiq.errors import (
    E_ASSIGN_WHILE_BORROWED,
    E_BORROW_CONFLICT,
    E_BORROW_MUT_IMMUTABLE,
    E_MOVE_WHILE_BORROWED,
)
from rustiq.pipeline import parse_source
from rustiq.semantic.analyzer import Analyzer


def error_codes(source: str) -> list[tuple[str, int, int]]:
    """Errores del Analyzer real (sin codegen, que aún no emite literales)."""
    tree, syntax_errors = parse_source(source)
    assert syntax_errors == []
    _, errors = Analyzer().analyze(tree)
    return [(e.code, e.line, e.column) for e in errors]

PUNTO = "struct Punto { x: i32, y: i32 }\nfn usar(p: Punto) {}\nfn leer(r: &i32) -> bool { true }\n"


def test_asignar_mientras_esta_prestado():
    src = "fn main() {\n    let mut x = 5;\n    let r = &x;\n    x = 10;\n}"
    assert error_codes(src) == [(E_ASSIGN_WHILE_BORROWED, 4, 5)]


def test_el_prestamo_muere_al_cerrar_su_bloque():
    src = "fn main() {\n    let mut x = 5;\n    {\n        let r = &x;\n    }\n    x = 6;\n}"
    assert error_codes(src) == []


def test_un_argumento_prestado_no_queda_prestado():
    src = PUNTO + "fn main() {\n    let mut x = 5;\n    let b = leer(&x);\n    x = 6;\n}"
    assert error_codes(src) == []


def test_el_prestamo_de_una_condicion_no_llega_al_cuerpo():
    src = PUNTO + "fn main() {\n    let mut x = 5;\n    if leer(&x) {\n        x = 6;\n    }\n}"
    assert error_codes(src) == []


def test_mover_mientras_esta_prestado():
    src = PUNTO + "fn main() {\n    let a = Punto { x: 1, y: 2 };\n    let r = &a;\n    usar(a);\n}"
    assert error_codes(src) == [(E_MOVE_WHILE_BORROWED, 7, 10)]


def test_mut_despues_de_compartido():
    src = "fn main() {\n    let mut x = 5;\n    let a = &x;\n    let b = &mut x;\n}"
    assert error_codes(src) == [(E_BORROW_CONFLICT, 4, 13)]


def test_compartido_despues_de_mut():
    src = "fn main() {\n    let mut x = 5;\n    let a = &mut x;\n    let b = &x;\n}"
    assert error_codes(src) == [(E_BORROW_CONFLICT, 4, 13)]


def test_varios_compartidos():
    src = "fn main() {\n    let x = 5;\n    let a = &x;\n    let b = &x;\n}"
    assert error_codes(src) == []


def test_mut_de_un_inmutable():
    src = "fn main() {\n    let x = 5;\n    let a = &mut x;\n}"
    assert error_codes(src) == [(E_BORROW_MUT_IMMUTABLE, 3, 13)]
