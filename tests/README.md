# Pruebas

## Programas `.rq`

- `valid/<nombre>.rq` con `valid/<nombre>.out`: la salida exacta esperada. Cada `print_*` imprime una línea. Sin `.out` la prueba se omite.
- `invalid/<nombre>.rq`: la primera línea es `// ERROR <fase> <codigo> <linea>:<columna>`, por ejemplo `// ERROR semantico E_USE_AFTER_MOVE 12:5`.

El runner (`runner.py`) compara fase, código, línea y columna del primer error. El mensaje puede cambiar sin romper pruebas. Con un error nunca se devuelve wasm.

`test_suite.py` depende de `rustiq.pipeline.compile_source` (A) y `rustiq.host.run_wasm(wasm: bytes) -> str` (B). Mientras el pipeline lance `NotImplementedError`, los casos se omiten. Cuando exista, quitar ese `except`.
