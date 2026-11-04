# Representación en memoria

Contrato 5 del plan. Lo mantiene la Persona A. Si se cambia algo aquí, se documenta antes de tocar el código.

## Modelo

Wasm solo maneja números (`i32`, `f64`). Todo valor compuesto vive en la memoria lineal y se maneja por su dirección, un `i32`.

## Tabla de representaciones

| Tipo | Representación en Wasm |
| --- | --- |
| `i32`, `bool`, `char` | `i32` en local |
| `f64` | `f64` en local |
| `String` | Puntero a `[len: i32][bytes UTF-8]` |
| Struct, tupla | Puntero a los campos en orden de declaración, cada uno en una ranura de 8 bytes |
| Array | Puntero a `n` ranuras de 8 bytes |
| Enum | Puntero a `[tag: i32][relleno][payload en ranuras de 8 bytes]`. El tag es el índice de la variante: 0, 1, 2... |
| Referencia (`&T`, `&mut T`) | `i32` con la dirección del valor |
| Escalar con `&` aplicado | Vive en una celda del heap. El local guarda su dirección (`Symbol.address_taken`) |

## Heap

- Bump allocator que empieza en la dirección 1024. Las direcciones menores se reservan para datos estáticos (literales de String).
- Un global mutable `$heap` que solo avanza.
- Si el heap se agota, se llama a `memory.grow`.
- No se libera memoria. Un loop que cree muchos `String` consume heap sin recuperarlo.

```wat
(global $heap (mut i32) (i32.const 1024))
(func $alloc (param $n i32) (result i32)
  (local $p i32)
  (local.set $p (global.get $heap))
  (global.set $heap (i32.add (global.get $heap) (local.get $n)))
  (local.get $p))
```

## ABI del módulo

- Exporta `memory` y `main`.
- Importa desde `env`: `print_i32`, `print_f64`, `print_bool`, `print_char`, `print_str`.
- El host se implementa dos veces con el mismo comportamiento: Python (`rustiq/host.py`) y navegador (`web/host.js`).

## Pendiente

- Tamaño exacto del relleno del enum y alineación del payload.
- Cómo se copian arrays y tuplas `Copy` (`memcpy`).
