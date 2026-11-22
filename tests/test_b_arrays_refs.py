"""Arrays y referencias a escalares (celdas con address_taken), con el pipeline real."""

from rustiq.errors import E_BAD_INDEX, E_TYPE_MISMATCH, E_USE_AFTER_MOVE
from rustiq.host import run_wasm
from rustiq.pipeline import compile_source

PUNTO = "struct Punto { x: i32, y: i32 }\n"


def errores(source: str) -> list[tuple[str, int, int]]:
    return [(e.code, e.line, e.column) for e in compile_source(source).errors]


def salida(cuerpo: str, extra: str = "") -> str:
    result = compile_source(extra + "fn main() {\n" + cuerpo + "\n}")
    assert result.ok, result.errors
    return run_wasm(result.wasm)


def trap(cuerpo: str) -> bool:
    result = compile_source("fn main() {\n" + cuerpo + "\n}")
    assert result.ok, result.errors
    try:
        run_wasm(result.wasm)
    except Exception as e:  # wasmtime lanza Trap por `unreachable`
        return "unreachable" in str(e)
    return False


# --- Arrays: ejecución ----------------------------------------------------------


def test_leer_elementos():
    assert salida("let a = [10, 20, 30];\nprint_i32(a[0] + a[2]);") == "40\n"


def test_array_de_f64_e_indice_calculado():
    assert salida("let a = [1.5, 2.5];\nlet i = 1;\nprint_f64(a[i - 1] + a[i]);") == "4.0\n"


def test_asignar_elementos_y_compuesta():
    assert salida("let mut a = [1, 2, 3];\na[1] = 7;\na[2] += 10;\nprint_i32(a[1]);\nprint_i32(a[2]);") == "7\n13\n"


def test_array_de_structs_y_campo_de_elemento():
    src = "let mut ps = [Punto { x: 1, y: 2 }, Punto { x: 3, y: 4 }];\nps[1].x = 9;\nprint_i32(ps[1].x + ps[0].y);"
    assert salida(src, PUNTO) == "11\n"


def test_array_por_parametro_y_por_referencia():
    extra = "fn suma(a: [i32; 3]) -> i32 { a[0] + a[1] + a[2] }\nfn primero(a: &[i32; 3]) -> i32 { a[0] }\n"
    assert salida("let a = [1, 2, 3];\nprint_i32(primero(&a));\nprint_i32(suma(a));", extra) == "1\n6\n"


def test_indice_fuera_de_rango_al_ejecutar():
    assert trap("let a = [1, 2, 3];\nlet i = 3;\nprint_i32(a[i]);")


def test_indice_negativo_al_ejecutar():
    assert trap("let a = [1, 2, 3];\nlet i = 0 - 1;\nprint_i32(a[i]);")


# --- Arrays: errores -------------------------------------------------------------


def test_elementos_de_tipos_distintos():
    assert errores("fn main() {\n    let a = [1, true];\n}") == [(E_TYPE_MISMATCH, 2, 17)]


def test_indice_que_no_es_i32():
    assert errores("fn main() {\n    let a = [1, 2];\n    let x = a[true];\n}") == [(E_TYPE_MISMATCH, 3, 15)]


def test_indexar_algo_que_no_es_array():
    assert errores("fn main() {\n    let a = 1;\n    let x = a[0];\n}") == [(E_BAD_INDEX, 3, 15)]


def test_indice_literal_fuera_de_rango():
    assert errores("fn main() {\n    let a = [1, 2];\n    let x = a[2];\n}") == [(E_BAD_INDEX, 3, 15)]


def test_el_array_mueve_sus_elementos():
    src = PUNTO + "fn main() {\n    let p = Punto { x: 1, y: 2 };\n    let a = [p];\n    let q = p;\n}"
    assert errores(src) == [(E_USE_AFTER_MOVE, 5, 13)]


# --- Referencias a escalares -----------------------------------------------------


def test_leer_un_escalar_por_referencia():
    extra = "fn doble(r: &i32) -> i32 { *r * 2 }\n"
    assert salida("let x = 21;\nprint_i32(doble(&x));\nprint_i32(x);", extra) == "42\n21\n"


def test_la_referencia_ve_el_valor_actual():
    assert salida("let mut x = 1;\nx = 5;\nlet r = &x;\nprint_i32(*r);") == "5\n"


def test_escalar_en_celda_se_sigue_asignando():
    src = "let mut x = 1;\n{\n    let r = &x;\n    print_i32(*r);\n}\nx += 10;\nprint_i32(x);"
    assert salida(src) == "1\n11\n"


def test_referencia_a_f64_y_bool():
    assert salida("let f = 2.5;\nlet b = true;\nlet rf = &f;\nlet rb = &b;\nprint_f64(*rf);\nprint_bool(*rb);") == "2.5\ntrue\n"


def test_parametro_escalar_con_referencia():
    extra = "fn leer(r: &i32) -> i32 { *r }\nfn f(n: i32) -> i32 { leer(&n) + n }\n"
    assert salida("print_i32(f(4));", extra) == "8\n"


def test_referencia_a_un_campo_escalar():
    extra = PUNTO + "fn leer(r: &i32) -> i32 { *r }\n"
    assert salida("let p = Punto { x: 3, y: 4 };\nprint_i32(leer(&p.y));", extra) == "4\n"


def test_referencia_a_un_literal():
    assert salida("let r = &7;\nprint_i32(*r);") == "7\n"


def test_referencia_a_una_referencia():
    assert salida("let x = 3;\nlet r = &x;\nlet rr = &r;\nprint_i32(*(*rr));") == "3\n"
