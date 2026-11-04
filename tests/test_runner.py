"""Pruebas del propio runner."""

from tests.runner import ExpectedError, parse_expected_error


def test_cabecera_valida():
    src = "// ERROR semantico E_USE_AFTER_MOVE 12:5\nfn main() {}\n"
    assert parse_expected_error(src) == ExpectedError("semantico", "E_USE_AFTER_MOVE", 12, 5)


def test_sin_cabecera():
    assert parse_expected_error("fn main() {}\n") is None
    assert parse_expected_error("") is None


def test_cabecera_mal_formada():
    assert parse_expected_error("// ERROR semantico E_X 12\n") is None
    assert parse_expected_error("// ERROR semantico E_X a:b\n") is None
