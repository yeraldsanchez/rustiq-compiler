"""Structs y tuplas: declaración, literal y acceso a campo."""

from rustiq.errors import (
    E_BAD_OPERAND,
    E_MISSING_FIELD,
    E_REDECLARED,
    E_TYPE_MISMATCH,
    E_UNKNOWN_FIELD,
    E_UNKNOWN_TYPE,
)
from tests.support import analyze, error_codes, run

PUNTO = "struct Punto { x: i32, y: i32 }\n"


def test_literal_y_acceso_a_campos():
    src = PUNTO + "fn main() { let p = Punto { x: 3, y: 4 }; print_i32(p.x); print_i32(p.y); }"
    assert run(src) == ["3", "4"]


def test_campos_en_otro_orden_que_la_declaracion():
    src = PUNTO + "fn main() { let p = Punto { y: 4, x: 3 }; print_i32(p.x * 10 + p.y); }"
    assert run(src) == ["34"]


def test_campos_con_distintos_tipos():
    src = """
struct Mezcla { a: i32, b: f64, c: bool, d: char }
fn main() {
    let m = Mezcla { a: 1, b: 2.5, c: true, d: 'z' };
    print_i32(m.a); print_f64(m.b); print_bool(m.c); print_char(m.d);
}
"""
    assert run(src) == ["1", "2.5", "true", "z"]


def test_struct_anidado():
    src = PUNTO + """
struct Rect { origen: Punto, ancho: i32 }
fn main() {
    let r = Rect { origen: Punto { x: 1, y: 2 }, ancho: 9 };
    print_i32(r.origen.y);
    print_i32(r.ancho);
}
"""
    assert run(src) == ["2", "9"]


def test_struct_como_argumento_y_retorno():
    src = PUNTO + """
fn crear(a: i32) -> Punto { Punto { x: a, y: a + 1 } }
fn suma(p: Punto) -> i32 { p.x + p.y }
fn main() { print_i32(suma(crear(10))); }
"""
    assert run(src) == ["21"]


def test_struct_declarado_despues_de_su_uso():
    src = "fn main() { let p = Punto { x: 1, y: 2 }; print_i32(p.y); }\n" + PUNTO
    assert run(src) == ["2"]


def test_struct_sin_campos():
    assert run("struct Vacio {}\nfn main() { let v = Vacio {}; print_i32(1); }") == ["1"]


def test_literal_de_struct_en_parentesis_dentro_de_if():
    src = PUNTO + "fn main() { if (Punto { x: 1, y: 2 }).x == 1 { print_i32(1); } }"
    assert run(src) == ["1"]


def test_literal_de_tupla_tiene_su_tipo():
    tree, info, errors = analyze("fn main() { let t = (1, true); }")
    assert errors == []
    literal = _buscar(tree, "TupleLiteralContext")
    assert str(info.expr_type.get(literal)) == "(i32, bool)"


def _buscar(node, class_name):
    if type(node).__name__ == class_name:
        return node
    for child in getattr(node, "children", None) or []:
        found = _buscar(child, class_name)
        if found is not None:
            return found


def test_tupla_se_crea_y_se_pasa():
    src = "fn pasa(t: (i32, i32)) {}\nfn main() { pasa((1, 2)); print_i32(1); }"
    assert run(src) == ["1"]


def test_acceso_por_referencia_a_struct():
    src = PUNTO + "fn leer(p: &Punto) -> i32 { p.y }\nfn main() { print_i32(1); }"
    assert error_codes(src) == []


# --- Inválidos -----------------------------------------------------------------


def test_campo_inexistente_en_literal():
    src = PUNTO + "fn main() {\n    let p = Punto { x: 1, z: 2, y: 3 };\n}"
    assert error_codes(src) == [(E_UNKNOWN_FIELD, 3, 27)]


def test_campo_faltante():
    src = PUNTO + "fn main() {\n    let p = Punto { x: 1 };\n}"
    assert error_codes(src) == [(E_MISSING_FIELD, 3, 13)]


def test_campo_repetido_en_literal():
    src = PUNTO + "fn main() {\n    let p = Punto { x: 1, x: 2, y: 3 };\n}"
    assert error_codes(src) == [(E_REDECLARED, 3, 27)]


def test_tipo_de_campo_incorrecto():
    src = PUNTO + "fn main() {\n    let p = Punto { x: true, y: 3 };\n}"
    assert error_codes(src) == [(E_TYPE_MISMATCH, 3, 24)]


def test_struct_inexistente():
    assert error_codes("fn main() {\n    let p = Nada { x: 1 };\n}") == [(E_UNKNOWN_TYPE, 2, 13)]


def test_acceso_a_campo_inexistente():
    src = PUNTO + "fn main() {\n    let p = Punto { x: 1, y: 2 };\n    print_i32(p.w);\n}"
    assert error_codes(src) == [(E_UNKNOWN_FIELD, 4, 17)]


def test_campo_de_un_tipo_sin_campos():
    assert error_codes("fn main() {\n    let n = 1;\n    print_i32(n.x);\n}") == [(E_BAD_OPERAND, 3, 17)]


def test_struct_duplicado():
    assert error_codes(PUNTO + PUNTO + "fn main() {}") == [(E_REDECLARED, 2, 8)]


def test_campo_duplicado_en_la_declaracion():
    assert error_codes("struct S { a: i32, a: i32 }\nfn main() {}") == [(E_REDECLARED, 1, 20)]


def test_tipo_de_campo_desconocido():
    assert error_codes("struct S { a: Nada }\nfn main() {}") == [(E_UNKNOWN_TYPE, 1, 15)]
