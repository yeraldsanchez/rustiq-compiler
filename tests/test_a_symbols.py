"""rustiq/symbols.py: qué es cada identificador, para el tipo al pasar el mouse."""

from rustiq.pipeline import compile_source

PROGRAMA = """\
const N: i32 = 3;
fn suma(a: i32, b: i32) -> i32 { a + b }
fn main() {
    let mut x = suma(N, 2);
    x = x + 1;
    print_i32(x);
}
"""


def simbolos(source: str) -> dict[tuple[int, int], object]:
    return {(s.line, s.column): s for s in compile_source(source).symbols}


def test_variable_declarada_con_tipo_inferido():
    x = simbolos(PROGRAMA)[(4, 13)]
    assert (x.name, x.kind, x.type, x.mutable, x.declaration) == ("x", "local", "i32", True, True)


def test_usos_y_asignacion():
    s = simbolos(PROGRAMA)
    assert s[(5, 5)].name == "x" and s[(5, 5)].declaration is False  # lado izquierdo
    assert s[(5, 9)].type == "i32"


def test_parametros_y_constantes():
    s = simbolos(PROGRAMA)
    assert (s[(2, 9)].kind, s[(2, 9)].type) == ("param", "i32")
    assert (s[(1, 7)].kind, s[(4, 22)].kind) == ("const", "const")


def test_funciones_con_firma():
    s = simbolos(PROGRAMA)
    assert s[(2, 4)].type == "fn suma(a: i32, b: i32) -> i32"
    assert s[(2, 4)].declaration is True
    assert (s[(4, 17)].kind, s[(4, 17)].declaration) == ("func", False)
    assert s[(3, 4)].type == "fn main()"  # sin `-> ()`


def test_funcion_del_host():
    print_i32 = simbolos(PROGRAMA)[(6, 5)]
    assert print_i32.kind == "host"
    assert print_i32.type.startswith("fn print_i32(")


def test_llega_con_errores_semanticos():
    result = compile_source("fn main() {\n    let y: bool = 5;\n}\n")
    assert not result.ok
    y = {(s.line, s.column): s for s in result.symbols}[(2, 9)]
    assert (y.name, y.type) == ("y", "bool")


def test_vacio_con_errores_de_sintaxis():
    assert compile_source("fn main() {\n    let x = ;\n}\n").symbols == []


def test_ordenados_y_sin_repetir():
    posiciones = [(s.line, s.column) for s in compile_source(PROGRAMA).symbols]
    assert posiciones == sorted(set(posiciones))


TIPOS = """\
struct Punto { x: i32, y: i32 }
enum Forma { Nada, Cuadrado(i32) }
fn mover(p: Punto) -> Forma { Forma::Cuadrado(p.x) }
fn main() {
    let p = Punto { x: 1, y: 2 };
    match mover(p) {
        Forma::Cuadrado(l) => print_i32(l),
        _ => print_i32(0),
    }
}
"""


def test_struct_muestra_sus_campos():
    s = simbolos(TIPOS)
    assert s[(1, 8)].kind == "struct" and s[(1, 8)].declaration is True
    assert s[(1, 8)].type == "struct Punto {\n    x: i32,\n    y: i32,\n}"
    assert s[(3, 13)].type == s[(1, 8)].type  # en un tipo
    assert (s[(5, 13)].kind, s[(5, 13)].declaration) == ("struct", False)  # en un literal


def test_enum_y_variantes():
    s = simbolos(TIPOS)
    assert s[(2, 6)].type == "enum Forma {\n    Nada,\n    Cuadrado(i32),\n}"
    assert s[(3, 23)].kind == "enum"  # tipo de retorno
    assert (s[(3, 38)].kind, s[(3, 38)].type) == ("variant", "Forma::Cuadrado(i32)")  # valor
    assert (s[(7, 16)].kind, s[(7, 16)].type) == ("variant", "Forma::Cuadrado(i32)")  # patrón
