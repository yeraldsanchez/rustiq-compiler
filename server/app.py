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
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rustiq.pipeline import compile_source

WEB_DIR = Path(__file__).resolve().parent.parent / "web" / "dist"
# Un programa de clase cabe sobrado: el más largo de las pruebas tiene ~1 600.
MAX_SOURCE_CHARS = 20_000

# Cabeceras de seguridad para todas las respuestas (editor y API).
# - 'wasm-unsafe-eval': el worker instancia el módulo compilado.
# - style-src 'unsafe-inline': CodeMirror inyecta sus estilos en tiempo de ejecución.
# - frame-ancestors 'none': nadie puede incrustar el editor en un iframe.
CONTENT_SECURITY_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'wasm-unsafe-eval'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "connect-src 'self'",
    "worker-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'none'",
    "frame-ancestors 'none'",
])
SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
}


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


# /docs, /redoc y /openapi.json solo con RUSTIQ_DOCS=1: en el servidor público
# no hace falta publicar el mapa de la API.
DOCS_ENABLED = os.environ.get("RUSTIQ_DOCS") == "1"

app = FastAPI(
    title="RustiQ",
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)

# El editor y la API comparten origen, así que en producción CORS no hace falta
# y sin él ningún otro sitio puede usar el servidor desde el navegador de sus
# visitantes. Para abrir el editor desde otro origen, poner los orígenes
# separados por coma en RUSTIQ_CORS_ORIGINS (por ejemplo, http://localhost:5173).
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("RUSTIQ_CORS_ORIGINS", "").split(",")
    if origin.strip()
]
if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["POST"], allow_headers=["*"]
    )


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


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
