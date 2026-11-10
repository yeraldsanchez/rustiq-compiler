"""Casos de la gramática que dependen de decisiones de docs/decisiones.md."""

import pytest
from antlr4 import CommonTokenStream, InputStream

from rustiq.generated.RustiQLexer import RustiQLexer
from rustiq.generated.RustiQParser import RustiQParser


def _errores_sintacticos(source: str) -> int:
    parser = RustiQParser(CommonTokenStream(RustiQLexer(InputStream(source))))
    parser.removeErrorListeners()
    parser.program()
    return parser.getNumberOfSyntaxErrors()


@pytest.mark.parametrize("tipo", ["&&i32", "&&mut i32", "& &i32", "&mut &i32"])
def test_p10_referencia_a_referencia_en_tipos(tipo):
    assert _errores_sintacticos(f"fn f(r: {tipo}) {{}}") == 0


def test_p10_and_logico_sigue_funcionando():
    assert _errores_sintacticos("fn f() { let a = x && y; }") == 0


def test_t3_doble_prestamo_en_expresion_no_es_valido():
    # unary acepta un solo prefijo, así que &&x no está en la EBNF.
    assert _errores_sintacticos("fn f() { let r = &&x; }") > 0


@pytest.mark.parametrize("nombre", ["_temp", "_x1", "x_y"])
def test_p7_identificadores_con_guion_bajo(nombre):
    assert _errores_sintacticos(f"fn f() {{ let {nombre} = 5; }}") == 0


def test_p7_guion_bajo_solo_es_comodin():
    tokens = CommonTokenStream(RustiQLexer(InputStream("_")))
    tokens.fill()
    assert tokens.tokens[0].type == RustiQLexer.UNDERSCORE
