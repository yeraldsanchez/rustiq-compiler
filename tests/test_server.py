"""server/app.py: la forma de la respuesta de POST /compile."""

import base64

import pytest
from fastapi.testclient import TestClient

from server.app import MAX_SOURCE_CHARS, app
from tests.support import PROGRAMA_MINIMO

CAMPOS_ERROR = {"phase", "code", "message", "line", "column", "length"}


@pytest.fixture
def client():
    return TestClient(app)


def test_programa_valido(client):
    resp = client.post("/compile", json={"source": PROGRAMA_MINIMO})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["errors"] == []
    assert body["wat"].startswith("(module")
    assert base64.b64decode(body["wasm_base64"]).startswith(b"\0asm")


def test_error_sintactico(client):
    resp = client.post("/compile", json={"source": "fn main() {\n    let x = ;\n}\n"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert body["wat"] is None
    assert body["wasm_base64"] is None
    error = body["errors"][0]
    assert set(error) == CAMPOS_ERROR
    assert (error["phase"], error["code"], error["line"], error["column"]) == (
        "sintactico", "E_SYNTAX", 2, 13,
    )


def test_falta_source(client):
    assert client.post("/compile", json={}).status_code == 422


def test_source_demasiado_largo(client):
    resp = client.post("/compile", json={"source": "a" * (MAX_SOURCE_CHARS + 1)})
    assert resp.status_code == 422


def test_cors_permite_otro_origen(client):
    resp = client.options(
        "/compile",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "*"


def test_sirve_la_carpeta_web(client):
    assert client.get("/hola.html").status_code == 200


def test_devuelve_simbolos(client):
    resp = client.post("/compile", json={"source": "fn main() {\n    let x = 1;\n    print_i32(x);\n}\n"})
    simbolos = resp.json()["symbols"]
    assert {"name": "x", "kind": "local", "type": "i32"}.items() <= simbolos[1].items()
    assert simbolos[1]["line"] == 2 and simbolos[1]["column"] == 9
