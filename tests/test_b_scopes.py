"""Pruebas de ámbitos, sombreado, declaraciones locales y resolución de identificadores (Carril B)."""

from antlr4 import CommonTokenStream, InputStream

from rustiq.errors import E_REDECLARED, E_TYPE_MISMATCH, E_UNDECLARED
from rustiq.generated.RustiQLexer import RustiQLexer
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.analyzer import Analyzer
from rustiq.types import BOOL, F64, I32


def _analyze(source: str):
    lexer = RustiQLexer(InputStream(source))
    parser = RustiQParser(CommonTokenStream(lexer))
    tree = parser.program()
    assert parser.getNumberOfSyntaxErrors() == 0
    return Analyzer().analyze(tree)


# ---------------------------------------------------------------
# Casos válidos: ámbitos, sombreado (G2) e inferencia en let
# ---------------------------------------------------------------

def test_sombreado_en_bloque_interno_asigna_uid_distinto():
    src = """
    fn f(p_i32: i32, p_bool: bool) {
        let x: i32 = p_i32;
        {
            let x: bool = p_bool;
            let y: bool = x;
        }
        let z: i32 = x;
    }
    fn main() {}
    """
    info, errors = _analyze(src)
    assert errors == []

    simbolos_x = [
        sym for sym in info.symbol._values.values()
        if sym.name == "x" and sym.kind == "local"
    ]
    uids = {sym.uid for sym in simbolos_x}
    tipos = {sym.uid: sym.type for sym in simbolos_x}

    assert len(uids) == 2
    assert set(tipos.values()) == {I32, BOOL}


def test_sombreado_de_parametro_en_bloque_interno():
    src = """
    fn f(a: i32, otro: f64) -> i32 {
        {
            let a: f64 = otro;
        }
        return a;
    }
    fn main() {}
    """
    info, errors = _analyze(src)
    assert errors == []


def test_inferencia_let_y_let_sin_inicializador():
    src = """
    fn f(p: i32) {
        let a: i32 = p;
        let b = a;
        let mut c: bool;
    }
    fn main() {}
    """
    info, errors = _analyze(src)
    assert errors == []


# ---------------------------------------------------------------
# Casos inválidos: errores de ámbito y declaraciones (G2, T4)
# ---------------------------------------------------------------

def test_error_variable_no_declarada():
    src = """
    fn main() {
        let a: i32 = x;
    }
    """
    _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].phase == "semantico"
    assert errors[0].code == E_UNDECLARED


def test_error_variable_fuera_de_su_bloque():
    src = """
    fn main() {
        {
            let interna: i32;
        }
        let fuera: i32 = interna;
    }
    """
    _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].phase == "semantico"
    assert errors[0].code == E_UNDECLARED


def test_error_redeclaracion_mismo_ambito():
    src = """
    fn main() {
        let x: i32;
        let x: i32;
    }
    """
    _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].phase == "semantico"
    assert errors[0].code == E_REDECLARED


def test_error_redeclaracion_con_parametro_en_cuerpo_funcion():
    src = """
    fn f(x: i32) {
        let x: i32;
    }
    fn main() {}
    """
    _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].phase == "semantico"
    assert errors[0].code == E_REDECLARED


def test_error_let_sin_tipo_ni_inicializador():
    src = """
    fn main() {
        let x;
    }
    """
    _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].phase == "semantico"
    assert errors[0].code == E_TYPE_MISMATCH


def test_error_let_tipo_incompatible_con_inicializador():
    src = """
    fn f(a: bool) {
        let b: i32 = a;
    }
    fn main() {}
    """
    _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].phase == "semantico"
    assert errors[0].code == E_TYPE_MISMATCH

# ---------------------------------------------------------------
# Sin errores en cascada: una variable con error previo queda declarada
# ---------------------------------------------------------------

def test_variable_con_inicializador_erroneo_no_genera_cascada():
    src = """
    fn main() {
        let a = nada;
        let b = a;
        let c = a;
    }
    """
    _, errors = _analyze(src)
    assert [e.code for e in errors] == [E_UNDECLARED]


def test_let_sin_tipo_ni_inicializador_no_genera_cascada():
    src = """
    fn main() {
        let x;
        let y = x;
    }
    """
    _, errors = _analyze(src)
    assert [e.code for e in errors] == [E_TYPE_MISMATCH]
