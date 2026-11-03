# Decisiones del lenguaje

Qué se soporta, qué no, y en qué se diferencia RustiQ de Rust. Se actualiza en el mismo PR que cambie una decisión.

Estado: **por defecto** = asumido por el plan, sin confirmar. **confirmado** = respondido por el profesor o acordado por el grupo.

## Decisiones del grupo

| # | Tema | Decisión | Estado |
| --- | --- | --- | --- |
| G1 | Tipos `Copy` | Regla de Rust: `i32`, `f64`, `bool`, `char` y `&T` son Copy. `&mut T`, `String`, structs y enums se mueven. Array o tupla es Copy solo si todos sus elementos lo son | por defecto |
| G2 | Sombreado | Prohibido en el mismo ámbito, permitido en ámbitos internos | por defecto |
| G3 | Memoria | Bump allocator sin liberar, con `memory.grow`. Ver `memoria.md` | por defecto |
| G4 | Alcance de `String` | Crear, mover, pasar, retornar e imprimir. Sin concatenación ni comparación | por defecto (depende de P9) |

## Puntos para el profesor

| # | Tema | Decisión asumida | Estado |
| --- | --- | --- | --- |
| P1 | Salida | Funciones builtin `print_i32`, `print_f64`, `print_bool`, `print_char`, `print_str` importadas del host | por defecto |
| P2 | `t.0` en tuplas | No existe. Las tuplas se leen con `match` | por defecto |
| P3 | `*r = valor` | No existe. `&mut` sirve para structs y arrays | por defecto |
| P4 | `if` como expresión | Solo sentencia | por defecto |
| P5 | `match` sin `;` en medio de un bloque | Se exige `;` | por defecto |
| P6 | Patrones negativos | No permitidos | por defecto |
| P7 | Identificadores con `_` inicial | No permitidos. `_` es solo el comodín | por defecto |
| P8 | Conversión `i32` y `f64` | No existe | por defecto |
| P9 | Operaciones sobre `String` | Crear, mover, pasar, imprimir | por defecto |

## Ajustes técnicos de ANTLR

| # | Tema | Decisión |
| --- | --- | --- |
| T1 | Struct literal contra bloque | Prohibido en condiciones de `if`, `while` y en el valor de `match`. Se usa entre paréntesis |
| T2 | Comparaciones encadenadas | `a < b < c` es error sintáctico, igual que en Rust |
| T3 | `&&x` | Se intenta tratar como dos préstamos. Si no hay tiempo, no soportado |
| T4 | `let` sin inicializador | Válido si el tipo se indica y se asigna antes de usarse. Reutiliza el estado "sin inicializar" de movimientos |

## Soportado

_Por completar al cierre de cada etapa._

## Parcial

_Por completar._

## No soportado

_Por completar._

## Diferencias con Rust

- Todo movimiento condicional se trata como definitivo (más estricto que Rust), si el análisis de ramas se recorta.
- El préstamo vive hasta el final del ámbito léxico donde se creó, sin análisis de último uso.
- No hay liberación de memoria (`drop`).
- Patrones anidados de un solo nivel, si el codegen lo exige.
