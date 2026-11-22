"""Servidor del editor: expone el compilador por HTTP. Dueño: A (Yerald).

Contrato 6 del plan:

    POST /compile  { "source": "..." }
    → { "ok": true,  "errors": [], "wat": "...", "wasm_base64": "..." }
    → { "ok": false, "errors": [CompileError...], "wat": null, "wasm_base64": null }

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


class CompileResponse(BaseModel):
    ok: bool
    errors: list[ErrorOut]
    wat: str | None
    wasm_base64: str | None


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
    )


# Va al final: el mount en "/" no debe tapar las rutas de la API.
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
