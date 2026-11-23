"""Servidor del editor: expone el compilador por HTTP.

    POST /compile  { "source": "..." }
    → { "ok": true,  "errors": [], "wat": "...", "wasm_base64": "...", "symbols": [...] }
    → { "ok": false, "errors": [CompileError...], "wat": null, "wasm_base64": null, "symbols": [...] }

`symbols` es una extensión para el editor (tipo al pasar el mouse): qué es
cada identificador. Llega aunque haya errores semánticos.

También sirve el editor ya construido (`web/dist/`) en `/`, así el editor y
la API comparten origen. `web/dist/` está en el repo para no necesitar Node;
se regenera con `npm run build` dentro de `web/`. Se levanta con:

    uvicorn server.app:app --reload
"""

import base64
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rustiq.pipeline import compile_source

WEB_DIR = Path(__file__).resolve().parent.parent / "web" / "dist"
MAX_SOURCE_CHARS = 100_000


class CompileRequest(BaseModel):
    source: str = Field(max_length=MAX_SOURCE_CHARS)


class ErrorOut(BaseModel):
    """Forma JSON de `rustiq.errors.CompileError`."""

    phase: str
    code: str
    message: str
    line: int
    column: int
    length: int


class SymbolOut(BaseModel):
    """Forma JSON de `rustiq.symbols.SymbolHint`."""

    line: int
    column: int
    length: int
    name: str
    kind: str
    type: str | None
    mutable: bool
    declaration: bool
    id: str


class CompileResponse(BaseModel):
    ok: bool
    errors: list[ErrorOut]
    wat: str | None
    wasm_base64: str | None
    symbols: list[SymbolOut] = []


app = FastAPI(title="RustiQ")

# Permite abrir el editor desde otro origen (otro puerto o file://) mientras se
# desarrolla. La API no usa cookies ni credenciales.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST"], allow_headers=["*"])


@app.post("/compile", response_model=CompileResponse)
def compile_endpoint(request: CompileRequest) -> CompileResponse:
    result = compile_source(request.source)
    wasm_base64 = base64.b64encode(result.wasm).decode("ascii") if result.wasm else None
    return CompileResponse(
        ok=result.ok,
        errors=[ErrorOut(**e.to_dict()) for e in result.errors],
        wat=result.wat,
        wasm_base64=wasm_base64,
        symbols=[SymbolOut(**s.to_dict()) for s in result.symbols],
    )


# Va al final: el mount en "/" no debe tapar las rutas de la API.
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
