;; Módulo mínimo a mano: sigue la ABI de docs/memoria.md.
;; Exporta `memory` y `main`, e importa print_i32 desde `env`.
(module
  (import "env" "print_i32" (func $print_i32 (param i32)))
  (memory (export "memory") 1)
  (func (export "main")
    i32.const 42
    call $print_i32))
