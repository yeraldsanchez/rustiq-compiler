"""Emisor base: módulo, funciones, parámetros, retorno y export de main."""

from antlr4 import CommonTokenStream, InputStream

from rustiq.codegen.emitter import Emitter
from rustiq.codegen.wasm_types import wasm_type
from rustiq.errors import E_REDECLARED, E_UNKNOWN_TYPE
from rustiq.generated.RustiQLexer import RustiQLexer
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.pipeline import assemble
from rustiq.semantic.analyzer import Analyzer
from rustiq.types import BOOL, F64, I32, STRING, UNIT, ArrayT, RefT, StructT, TupleT


def _analyze(source: str):
    parser = RustiQParser(CommonTokenStream(RustiQLexer(InputStream(source))))
    tree = parser.program()
    assert parser.getNumberOfSyntaxErrors() == 0
    info, errors = Analyzer().analyze(tree)
    return tree, info, errors


def _wat(source: str) -> str:
    tree, info, errors = _analyze(source)
    assert errors == []
    return Emitter(info).generate(tree)


def test_wasm_type():
    assert wasm_type(F64) == "f64"
    for t in (I32, BOOL, STRING, ArrayT(I32, 2), TupleT((I32,)), RefT(F64, False), StructT("P")):
        assert wasm_type(t) == "i32"


def test_main_vacio_se_exporta_y_valida():
    wat = _wat("fn main() {}")
    assert '(func $f_main (export "main")' in wat
    assemble(wat)


def test_firma_con_parametros_y_retorno():
    wat = _wat("fn f(a: i32, b: f64) -> bool { return true; }\nfn main() {}")
    assert "(func $f_f (param $a_0 i32) (param $b_1 f64) (result i32)" in wat


def test_funcion_unit_no_tiene_result():
    wat = _wat("fn g(a: i32) {}\nfn main() {}")
    assert "(func $f_g (param $a_0 i32)\n" in wat


def test_varias_funciones_sin_main_en_el_nombre_no_se_exportan():
    wat = _wat("fn g() {}\nfn main() {}")
    assert wat.count("(export \"main\")") == 1


def test_firmas_registradas():
    _, info, _ = _analyze(
        "struct P { x: i32 }\nfn f(p: &mut P, xs: [i32; 3]) -> (i32, f64) { loop {} }\nfn main() {}"
    )
    sig = info.functions["f"]
    assert sig.params == [("p", RefT(StructT("P"), True)), ("xs", ArrayT(I32, 3))]
    assert sig.ret == TupleT((I32, F64))
    assert info.functions["f"].ret != UNIT


def test_funcion_duplicada():
    _, _, errors = _analyze("fn f() {}\nfn f() {}\nfn main() {}")
    assert [e.code for e in errors] == [E_REDECLARED]


def test_tipo_desconocido():
    _, _, errors = _analyze("fn f(a: Foo) {}\nfn main() {}")
    assert [e.code for e in errors] == [E_UNKNOWN_TYPE]
    assert (errors[0].line, errors[0].column) == (1, 9)


def test_locales_y_etiquetas():
    tree, info, _ = _analyze("fn main() {}")
    emitter = Emitter(info)
    emitter.generate(tree)
    from rustiq.codegen.emitter import FunctionCtx
    emitter._fn = FunctionCtx("main")
    assert emitter.new_label("loop") == "$loop1"
    assert emitter.new_label("block") == "$block2"
    assert emitter.new_temp(F64) == "$tmp1"
    assert emitter.fn.locals == {"$tmp1": "f64"}


def test_heap_por_defecto_en_1024():
    wat = _wat('fn main() { let s = "hola"; }')
    assert '(memory (export "memory") 1)' in wat
    assert "(global $heap (mut i32) (i32.const 1024))" in wat


def test_literales_grandes_mueven_el_heap_y_agrandan_la_memoria():
    # Los literales ocupan 70001 bytes desde la dirección 0; alineado a 8, el heap empieza en 70008
    wat = _wat('fn main() { let s = "' + "a" * 70001 + '"; }')
    assert '(memory (export "memory") 2)' in wat
    assert "(global $heap (mut i32) (i32.const 70008))" in wat
    assemble(wat)
