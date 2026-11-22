"""Asignación: mutabilidad, tipos, campos y reinicialización, con el pipeline real."""

from rustiq.errors import E_ASSIGN_IMMUTABLE, E_BAD_OPERAND, E_TYPE_MISMATCH, E_UNDECLARED, E_UNKNOWN_FIELD
from rustiq.host import run_wasm
from rustiq.pipeline import compile_source

PUNTO = "struct Punto { x: i32, y: i32 }\n"


def errores(source: str) -> list[tuple[str, int, int]]:
    return [(e.code, e.line, e.column) for e in compile_source(source).errors]


def salida(source: str) -> str:
    result = compile_source(source)
    assert result.ok, result.errors
    return run_wasm(result.wasm)


# --- Errores -------------------------------------------------------------------


def test_asignar_a_un_inmutable():
    assert errores("fn main() {\n    let x = 1;\n    x = 2;\n}") == [(E_ASSIGN_IMMUTABLE, 3, 5)]


def test_primera_asignacion_de_un_let_sin_valor_no_pide_mut():
    assert errores("fn main() {\n    let x: i32;\n    x = 2;\n    print_i32(x);\n}") == []


def test_segunda_asignacion_de_un_let_sin_valor_si_pide_mut():
    src = "fn main() {\n    let x: i32;\n    x = 2;\n    x = 3;\n}"
    assert errores(src) == [(E_ASSIGN_IMMUTABLE, 4, 5)]


def test_asignar_un_tipo_distinto():
    assert errores("fn main() {\n    let mut x = 1;\n    x = true;\n}") == [(E_TYPE_MISMATCH, 3, 9)]


def test_asignacion_compuesta_solo_con_numeros():
    assert errores("fn main() {\n    let mut b = true;\n    b += false;\n}") == [(E_BAD_OPERAND, 3, 7)]


def test_asignar_a_una_variable_no_declarada():
    assert errores("fn main() {\n    x = 1;\n}") == [(E_UNDECLARED, 2, 5)]


def test_asignar_a_un_campo_inexistente():
    src = PUNTO + "fn main() {\n    let mut p = Punto { x: 1, y: 2 };\n    p.z = 3;\n}"
    assert errores(src) == [(E_UNKNOWN_FIELD, 4, 7)]


def test_asignar_un_campo_de_un_struct_inmutable():
    src = PUNTO + "fn main() {\n    let p = Punto { x: 1, y: 2 };\n    p.x = 3;\n}"
    assert errores(src) == [(E_ASSIGN_IMMUTABLE, 4, 5)]


def test_asignar_un_campo_a_traves_de_mut_ref():
    src = PUNTO + "fn mover(p: &mut Punto) {\n    p.x = 3;\n}\nfn main() {}"
    assert errores(src) == []


# --- Ejecución -----------------------------------------------------------------


def test_asignacion_simple_y_compuesta():
    src = "fn main() {\n    let mut x = 1;\n    x += 4;\n    x *= 3;\n    print_i32(x);\n    x = 7;\n    print_i32(x);\n}"
    assert salida(src) == "15\n7\n"


def test_asignacion_compuesta_f64():
    assert salida("fn main() {\n    let mut x = 1.5;\n    x /= 2.0;\n    print_f64(x);\n}") == "0.75\n"


def test_asignar_campos():
    src = PUNTO + "fn main() {\n    let mut p = Punto { x: 1, y: 2 };\n    p.x = 10;\n    p.y -= 5;\n    print_i32(p.x);\n    print_i32(p.y);\n}"
    assert salida(src) == "10\n-3\n"


def test_reinicializar_un_struct_movido():
    src = PUNTO + "fn usar(p: Punto) {\n    print_i32(p.x);\n}\nfn main() {\n    let mut a = Punto { x: 1, y: 2 };\n    usar(a);\n    a = Punto { x: 3, y: 4 };\n    usar(a);\n}"
    assert salida(src) == "1\n3\n"


def test_literales_char_y_bool():
    assert salida("fn main() {\n    print_char('\\n');\n    print_char('a');\n    print_bool(true);\n}") == "\n\na\ntrue\n"
