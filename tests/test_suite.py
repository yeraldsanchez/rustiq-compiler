"""Suite de regresión: todos los programas de tests/valid y tests/invalid."""

import pytest

from tests import runner


def _compile_source():
    from rustiq.pipeline import compile_source

    return compile_source


@pytest.mark.parametrize("rq", runner.valid_cases(), ids=lambda p: p.stem)
def test_valido(rq):
    if not rq.with_suffix(".out").exists():
        pytest.skip("sin .out todavía")
    from rustiq.host import run_wasm  # B (Byron)

    try:
        runner.check_valid(rq, _compile_source(), run_wasm)
    except NotImplementedError as e:
        pytest.skip(str(e))


@pytest.mark.parametrize("rq", runner.invalid_cases(), ids=lambda p: p.stem)
def test_invalido(rq):
    try:
        runner.check_invalid(rq, _compile_source())
    except NotImplementedError as e:
        pytest.skip(str(e))
