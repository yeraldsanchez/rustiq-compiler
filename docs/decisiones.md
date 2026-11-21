# Decisiones del lenguaje

Qué se soporta, qué no, y en qué se diferencia RustiQ de Rust. Se actualiza en el mismo PR que cambie una decisión.

Estado: **por defecto** = asumido por el plan, sin confirmar. **confirmado** = respondido por el profesor o acordado por el grupo.

## Decisiones del grupo

Criterio del grupo (16 de noviembre de 2026): en cada decisión abierta se elige la opción más sencilla que cumpla el enunciado, aunque sea más restrictiva que Rust.

| # | Tema | Decisión | Estado |
| --- | --- | --- | --- |
| G1 | Tipos `Copy` | Solo `i32`, `f64`, `bool`, `char`, `()` y `&T` son Copy. Todo lo que vive en el heap se mueve: `String`, arrays, tuplas, structs y enums, igual que `&mut T`. Así una copia nunca necesita `memcpy` | confirmado |
| G2 | Sombreado | Prohibido en el mismo ámbito, permitido en ámbitos internos. Es la regla base del enunciado, sin reglas de sombreado extra | confirmado |
| G3 | Memoria | Bump allocator sin liberar, con `memory.grow`. Ver `memoria.md` | confirmado |
| G5 | Ramas de `if` y cuerpo de `while`/`loop` | No producen valor (consecuencia de P4). Para devolver un valor desde un `if` se usa `return` | confirmado |
| G6 | Constantes | Las globales se expanden en cada uso y se pueden declarar en cualquier orden. No se verifica que su inicializador sea constante ni que no sea recursivo | confirmado |
| G7 | `main` | Obligatoria, sin parámetros y sin valor de retorno (`E_BAD_MAIN`) | confirmado |
| G8 | Movimientos en ramas y ciclos | Cada rama de un `if` empieza con el estado de antes del `if`. Después del `if`, la variable queda movida si se movió en cualquier rama. Reponerla dentro de una rama no cuenta, solo fuera del `if`. Mover dentro de un ciclo una variable declarada fuera de él es error | confirmado |
| G9 | Duración de los préstamos | Un préstamo guardado en una variable dura hasta el fin del bloque donde se declaró esa variable. Un préstamo temporal, como `f(&mut v)`, dura solo esa sentencia. Sin análisis de último uso | confirmado |
| G10 | Patrones anidados | Se permiten a cualquier profundidad, como dice la gramática. Un `match` es exhaustivo si tiene un brazo `_` o identificador; si es sobre un enum y aparecen todas sus variantes con subpatrones `_` o identificadores; o si es sobre `bool` y aparecen `true` y `false`. En cualquier otro caso se exige `_` | confirmado |
| G11 | Detalles de `match` | Una tupla de patrones `_` o identificadores también es irrefutable, así que `match p { (a, b) => ... }` es exhaustivo. Un identificador en un patrón siempre declara una variable nueva, aunque se llame como una constante. Un literal `String` no se acepta como patrón (G4). Los brazos repetidos o inalcanzables no se reportan. Un `match` sobre `&Enum` solo acepta `_` o un identificador hasta que existan las referencias. Un `match` sobre una variable la mueve solo si algún patrón liga un valor que no es Copy | por defecto |
| G4 | Alcance de `String` | Crear, mover, pasar, retornar e imprimir. Sin concatenación ni comparación | confirmado (P9) |

## Puntos para el profesor

Criterio del profesor (9 de noviembre de 2026): la gramática se sigue tal como está, aunque sea más restrictiva que Rust. Solo se agrega algo si se justifica que, sin eso, otra parte de la gramática no funcionaría.

| # | Tema | Decisión asumida | Estado |
| --- | --- | --- | --- |
| P1 | Salida | Funciones builtin `print_i32`, `print_f64`, `print_bool`, `print_char`, `print_str` importadas del host | confirmado |
| P2 | `t.0` en tuplas | No existe. Las tuplas se leen con `match` | confirmado |
| P3 | `*r = valor` | No existe. `&mut` sirve para structs y arrays | confirmado |
| P4 | `if` como expresión | Solo sentencia | confirmado |
| P5 | `match` sin `;` en medio de un bloque | Se exige `;` | confirmado |
| P6 | Patrones negativos | No permitidos | confirmado |
| P7 | Identificadores con `_` inicial | Se siguen las reglas léxicas, como ya hace el lexer. Pueden empezar con letra o `_` (`_temp`). `_` solo es el comodín | confirmado |
| P8 | Conversión `i32` y `f64` | No existe | confirmado |
| P9 | Operaciones sobre `String` | Crear, mover, pasar, retornar e imprimir. Sin concatenación ni comparación | confirmado |
| P10 | `&&T` sin espacio | Soportado en tipos: `&&T` equivale a `& &T`. La EBNF ya lo permite | confirmado |

## Ajustes técnicos de ANTLR

| # | Tema | Decisión |
| --- | --- | --- |
| T1 | Struct literal contra bloque | Prohibido en condiciones de `if`, `while` y en el valor de `match`. Se usa entre paréntesis |
| T2 | Comparaciones encadenadas | `a < b < c` es error sintáctico, igual que en Rust |
| T3 | `&&x` | No soportado. `unary` acepta un solo prefijo, así que la EBNF tampoco permite `& &x` |
| T4 | `let` sin inicializador | Válido si el tipo se indica y se asigna antes de usarse. Reutiliza el estado "sin inicializar" de movimientos |

## Soportado

_Por completar al cierre de cada etapa._

## Parcial

_Por completar._

## No soportado

_Por completar._

## Diferencias con Rust

- Los arrays y las tuplas siempre se mueven (G1). En Rust son Copy si todos sus elementos lo son.
- Una variable movida dentro de una rama no se repone aunque se le asigne un valor nuevo en esa misma rama (G8). Rust sí la repone si se reasigna en todos los caminos.
- Un préstamo guardado en una variable vive hasta el fin del bloque de esa variable, aunque ya no se use (G9). Rust lo termina en su último uso.
- Un `match` con patrones anidados refutables necesita un brazo `_` (G10). Rust calcula la exhaustividad exacta.
- Un brazo de `match` cuyo cuerpo termina en `return` o `break` tiene tipo `()`, porque RustiQ no tiene el tipo `!` de Rust. Si los otros brazos producen un valor, es error de tipos.
- Rust avisa de brazos inalcanzables en un `match`; RustiQ no.
- Mover dentro de un ciclo una variable declarada fuera es error aunque después venga `break` o `return` (G8). Rust lo permite si el ciclo no vuelve a usarla.
- No hay liberación de memoria (`drop`).
