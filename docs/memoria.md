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
| Enum | Puntero a `[tag: i32][relleno de 4 bytes][payload...]`. El tag y su relleno ocupan la ranura 0 (offset 0) y cada dato del payload una ranura de 8 bytes desde la 1 (offset 8, 16...). El tag es el índice de la variante: 0, 1, 2... Una variante sin datos ocupa 8 bytes |
| Referencia (`&T`, `&mut T`) | `i32` con la dirección del valor |
| Escalar con `&` aplicado | Vive en una celda de 8 bytes del heap (`Symbol.address_taken`). El local `$x_uid_cell` guarda su dirección; un parámetro se copia a su celda al entrar a la función |

Una referencia a un struct, tupla o array es el mismo puntero que el valor, así que `p.x` con `p: &Punto` no carga nada extra. El acceso a campo y el indexado quitan un nivel de referencia.

Una referencia a un escalar es la dirección de su celda, y `*r` la lee con `load`. `&p.x` y `&a[i]` dan la dirección de la ranura. `&5` o `&f()` guardan el valor en una celda nueva.

Cada `a[i]` revisa `i` con `i32.ge_u` contra el tamaño (un negativo también queda fuera) y hace `unreachable` si se sale. Un índice literal fuera de rango es error de compilación (`E_BAD_INDEX`).

## Heap

- Bump allocator. Los literales de String van desde la dirección 0 y el heap empieza en 1024, o justo después de los literales (alineado a 8) si ocupan más. Si hace falta, la memoria inicial tiene más de una página.
- Un global mutable `$heap` que solo avanza.
- Si el heap se agota, se llama a `memory.grow`.
- No se libera memoria. Un loop que cree muchos `String` consume heap sin recuperarlo.

Implementación en `rustiq/codegen/runtime.wat`. El Emitter la pega dentro de cada módulo:

| Función | Qué hace |
| --- | --- |
| `$alloc(n) -> ptr` | Reserva `n` bytes redondeados a múltiplo de 8, así todo bloque queda alineado a 8. Si no cabe, llama a `memory.grow` con las páginas que falten. Si el grow falla, `unreachable` |
| `$memcpy(dst, src, n)` | Copia `n` bytes hacia adelante, byte por byte |
| `$str_new(src, len) -> ptr` | Crea `[len][bytes]` en el heap copiando `len` bytes desde `src` (un literal de la zona estática) |
| `$str_len(s)` | Lee el largo en bytes |
| `$str_data(s)` | Devuelve `s + 4`, la dirección del primer byte |

## ABI del módulo

- Exporta `memory` y `main`.
- Importa desde `env`: `print_i32`, `print_f64`, `print_bool`, `print_char`, `print_str`.
- El host se implementa dos veces con el mismo comportamiento: Python (`rustiq/host.py`) y navegador (`web/host.js`).
