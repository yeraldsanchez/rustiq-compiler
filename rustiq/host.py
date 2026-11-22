"""Minimal host module for running compiled Wasm modules.
The test suite only uses `run_wasm` to execute a compiled module and
retrieve the printed output. We provide a thin wrapper around wasmtime
that loads the module, creates a `Store`, and invokes the `_start`
function (or `main` if present). The function returns the stdout output
as a string so the tests can compare it against the expected `.out`
files.
"""

from __future__ import annotations

import wasmtime


def run_wasm(module_bytes: bytes) -> str:
    """Execute a compiled Wasm module and return its printed output."""
    out: list[str] = []
    engine = wasmtime.Engine()
    store = wasmtime.Store(engine)
    linker = wasmtime.Linker(engine)

    instance_ref: list[wasmtime.Instance] = []

    def host_print_i32(val: int) -> None:
        out.append(str(val))

    def host_print_f64(val: float) -> None:
        out.append(str(val))

    def host_print_bool(val: int) -> None:
        out.append("true" if val else "false")

    def host_print_char(val: int) -> None:
        out.append(chr(val))

    def host_print_str(ptr: int) -> None:
        mem = instance_ref[0].exports(store)["memory"]
        length = int.from_bytes(mem.read(store, ptr, ptr + 4), "little")
        text = bytes(mem.read(store, ptr + 4, ptr + 4 + length)).decode("utf-8")
        out.append(text)

    i32_t = wasmtime.ValType.i32()
    f64_t = wasmtime.ValType.f64()

    linker.define_func("env", "print_i32", wasmtime.FuncType([i32_t], []), host_print_i32)
    linker.define_func("env", "print_f64", wasmtime.FuncType([f64_t], []), host_print_f64)
    linker.define_func("env", "print_bool", wasmtime.FuncType([i32_t], []), host_print_bool)
    linker.define_func("env", "print_char", wasmtime.FuncType([i32_t], []), host_print_char)
    linker.define_func("env", "print_str", wasmtime.FuncType([i32_t], []), host_print_str)

    module = wasmtime.Module(engine, module_bytes)
    instance = linker.instantiate(store, module)
    instance_ref.append(instance)

    def invoke(name: str) -> None:
        exports = instance.exports(store)
        if name in exports:
            func = exports[name]
            if isinstance(func, wasmtime.Func):
                func(store)

    exports = instance.exports(store)
    invoke("_start") if "_start" in exports else invoke("main")
    return "\n".join(out) + "\n" if out else ""
