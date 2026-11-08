"""runtime.wat: allocator, memcpy y Strings, ejecutados en wasmtime."""

import subprocess

import pytest
from wasmtime import Engine, Instance, Module, Store

from rustiq.codegen.emitter import RUNTIME_WAT

PAGE = 65536
HEAP_START = 1024
LITERAL_ADDR = 16  # zona estática, por debajo del heap


def _instanciar(tmp_path, datos: bytes = b""):
    """Envuelve el runtime en un módulo que exporta sus funciones."""
    data = "".join(f"\\{b:02x}" for b in datos)
    wat = f"""(module
  (memory (export "memory") 1)
  {RUNTIME_WAT}
  (data (i32.const {LITERAL_ADDR}) "{data}")
  (export "alloc" (func $alloc))
  (export "memcpy" (func $memcpy))
  (export "str_new" (func $str_new))
  (export "str_len" (func $str_len))
  (export "str_data" (func $str_data)))
"""
    wat_file, wasm_file = tmp_path / "rt.wat", tmp_path / "rt.wasm"
    wat_file.write_text(wat, encoding="utf-8")
    subprocess.run(["wat2wasm", str(wat_file), "-o", str(wasm_file)], check=True)
    subprocess.run(["wasm-validate", str(wasm_file)], check=True)

    store = Store(Engine())
    instancia = Instance(store, Module(store.engine, wasm_file.read_bytes()), [])
    return store, instancia.exports(store)


def test_alloc_empieza_en_1024_y_alinea_a_8(tmp_path):
    store, ex = _instanciar(tmp_path)
    assert ex["alloc"](store, 5) == HEAP_START
    assert ex["alloc"](store, 8) == HEAP_START + 8
    assert ex["alloc"](store, 1) == HEAP_START + 16
    assert ex["alloc"](store, 0) == HEAP_START + 24
    assert ex["alloc"](store, 0) == HEAP_START + 24


def test_alloc_crece_la_memoria_si_no_cabe(tmp_path):
    store, ex = _instanciar(tmp_path)
    mem = ex["memory"]
    assert mem.size(store) == 1

    ptr = ex["alloc"](store, 2 * PAGE)
    assert ptr == HEAP_START
    assert mem.size(store) == 3  # 1024 + 128 KiB necesita 3 páginas

    # El último byte del bloque es escribible.
    mem.write(store, b"\x7f", ptr + 2 * PAGE - 1)
    assert mem.read(store, ptr + 2 * PAGE - 1, ptr + 2 * PAGE) == b"\x7f"


def test_alloc_justo_hasta_el_limite_no_crece(tmp_path):
    store, ex = _instanciar(tmp_path)
    ex["alloc"](store, PAGE - HEAP_START)
    assert ex["memory"].size(store) == 1


def test_memcpy_copia_n_bytes(tmp_path):
    store, ex = _instanciar(tmp_path)
    mem = ex["memory"]
    src, dst = ex["alloc"](store, 8), ex["alloc"](store, 8)
    mem.write(store, b"abcdefgh", src)

    ex["memcpy"](store, dst, src, 5)
    assert mem.read(store, dst, dst + 8) == b"abcde\x00\x00\x00"


@pytest.mark.parametrize("texto", ["hola", "año ✓", ""])
def test_str_new_copia_el_literal_al_heap(tmp_path, texto):
    datos = texto.encode("utf-8")
    store, ex = _instanciar(tmp_path, datos)
    mem = ex["memory"]

    s = ex["str_new"](store, LITERAL_ADDR, len(datos))
    assert s >= HEAP_START
    assert int.from_bytes(mem.read(store, s, s + 4), "little") == len(datos)
    assert ex["str_len"](store, s) == len(datos)
    data = ex["str_data"](store, s)
    assert data == s + 4
    assert bytes(mem.read(store, data, data + len(datos))).decode("utf-8") == texto


def test_dos_strings_no_se_pisan(tmp_path):
    store, ex = _instanciar(tmp_path, b"hola")
    mem = ex["memory"]
    a = ex["str_new"](store, LITERAL_ADDR, 4)
    b = ex["str_new"](store, LITERAL_ADDR, 4)
    assert b >= a + 8
    mem.write(store, b"X", ex["str_data"](store, b))
    assert mem.read(store, a + 4, a + 8) == b"hola"
