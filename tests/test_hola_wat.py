"""Prueba de humo del backend: WAT escrito a mano -> .wasm -> validación -> ejecución."""

import subprocess
from pathlib import Path

from wasmtime import Engine, Func, FuncType, Instance, Module, Store, ValType

HOLA_WAT = Path(__file__).parent / "wat" / "hola.wat"


def test_hola_wat_se_valida_y_ejecuta(tmp_path):
    wasm = tmp_path / "hola.wasm"
    subprocess.run(["wat2wasm", str(HOLA_WAT), "-o", str(wasm)], check=True)
    subprocess.run(["wasm-validate", str(wasm)], check=True)

    salida = []
    store = Store(Engine())
    modulo = Module(store.engine, wasm.read_bytes())
    print_i32 = Func(store, FuncType([ValType.i32()], []), salida.append)
    instancia = Instance(store, modulo, [print_i32])
    exports = instancia.exports(store)

    assert "memory" in exports
    exports["main"](store)
    assert salida == [42]
