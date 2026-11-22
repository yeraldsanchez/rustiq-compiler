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
| G9 | Duración de los préstamos | Un préstamo guardado en una variable dura hasta el fin del bloque donde se declaró esa variable. Mientras vive un `&mut`, el dueño no se puede leer, mover, asignar ni volver a prestar (`E_BORROW_CONFLICT`). Asignar `r = &x` es error si `x` se declaró en un bloque más interno que `r` (`E_DANGLING_REF`), y el préstamo vive lo que vive `r`. Un préstamo temporal, como `f(&mut v)`, dura hasta que vuelve la llamada si la función no devuelve una referencia (así `f(&mut v) + f(&mut v)` es válido), y si no, hasta el fin de la sentencia. Sin análisis de último uso | confirmado |
| G10 | Patrones anidados | Se permiten a cualquier profundidad, como dice la gramática. Un `match` es exhaustivo si tiene un brazo `_` o identificador; si es sobre un enum y aparecen todas sus variantes con subpatrones `_` o identificadores; o si es sobre `bool` y aparecen `true` y `false`. En cualquier otro caso se exige `_` | confirmado |
| G11 | Detalles de `match` | Una tupla de patrones `_` o identificadores también es irrefutable, así que `match p { (a, b) => ... }` es exhaustivo. Un identificador en un patrón siempre declara una variable nueva, aunque se llame como una constante. Un literal `String` no se acepta como patrón (G4). Los brazos repetidos o inalcanzables no se reportan. Un `match` sobre `&Enum` solo acepta `_` o un identificador hasta que existan las referencias. Un `match` sobre una variable la mueve solo si algún patrón liga un valor que no es Copy | por defecto |
| G12 | Mover partes de un valor | Mover un campo o un elemento que no es Copy (`f(p.nombre)`, `let t = a[0];`) mueve la variable entera: después no se puede usar ninguna parte de ella. Así el valor movido y su dueño nunca comparten memoria. Mover desde una referencia (`*r`, `r.campo` con `r: &T`) es error (`E_MOVE_OUT_OF_PLACE`). Leer campos Copy (`p.x`), prestar (`&p.campo`) e imprimir (`print_str(p.nombre)`) no mueven | confirmado |
| G13 | Formato de `print_f64` | El de `repr` de Python: un `f64` entero lleva `.0` (`3.0`), notación científica si el exponente es menor que -4 o mayor o igual que 16 (`1e-05`, `1e+16`), e `inf`, `-inf` y `nan`. Así un `f64` no se confunde con un `i32` en la salida. El host del navegador (`web/src/run/format.ts`) imprime igual que `rustiq/host.py` | confirmado |
| G4 | Alcance de `String` | Crear, mover, pasar, retornar e imprimir. Sin concatenación ni comparación | confirmado (P9) |

## Puntos para el profesor

Criterio del profesor (9 de noviembre de 2026): la gramática se sigue tal como está, aunque sea más restrictiva que Rust. Solo se agrega algo si se justifica que, sin eso, otra parte de la gramática no funcionaría.

| # | Tema | Decisión asumida | Estado |
| --- | --- | --- | --- |
| P1 | Salida | Funciones builtin `print_i32`, `print_f64`, `print_bool`, `print_char`, `print_str` importadas del host. Imprimir no mueve el valor: `print_str(s)` deja `s` disponible | confirmado |
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
| T1 | Struct literal contra bloque | Prohibido suelto en condiciones de `if`, `while` y en el valor de `match`. Se permite entre paréntesis, corchetes, llaves o como argumento de una llamada (`if suma(Punto { x: 1, y: 2 }) == 3`) |
| T2 | Comparaciones encadenadas | `a < b < c` es error sintáctico, igual que en Rust |
| T3 | `&&x` | No soportado. `unary` acepta un solo prefijo, así que la EBNF tampoco permite `& &x` |
| T4 | `let` sin inicializador | Válido si el tipo se indica y se asigna antes de usarse. Cuenta como asignada si se le asigna en todas las ramas de un `if` con `else` o de un `match` Reutiliza el estado "sin inicializar" de movimientos |
| T5 | Bloque anidado como valor final | ANTLR lee `{ { 3 } }` con el bloque interno como sentencia. Si la última sentencia de un bloque es otro bloque que produce valor y no hay otra expresión final, ese bloque es la expresión final (`flow.block_tail`) |
| T6 | Errores léxicos | El lexer tiene tokens de error en el canal oculto (`BAD_STRING`, `UNTERMINATED_STRING`, `BAD_CHAR`, `UNTERMINATED_CHAR`, `UNTERMINATED_COMMENT`). El parser no los ve y el pipeline los reporta como `E_UNTERMINATED_STRING`, `E_INVALID_ESCAPE`, `E_UNTERMINATED_COMMENT` o `E_INVALID_CHAR`, con la posición exacta |

## Soportado

**Léxico y sintaxis** (ANTLR4, `grammar/RustiQ.g4`, sigue la EBNF del profesor)

- Comentarios `//` y `/* */`. Literales `i32` (decimal), `f64` (`1.5`), `bool`, `char` y `String` con los escapes `\n \t \r \\ \" \'`, y Unicode dentro de `char` y `String`.
- Items: `fn`, `struct`, `enum` (variantes sin datos o con datos) y `const` global. Se pueden declarar en cualquier orden.
- Tipos: `i32`, `f64`, `bool`, `char`, `String`, arrays `[T; N]`, tuplas, `&T`, `&mut T`, `&&T` (P10), structs y enums.
- Sentencias: `let` con o sin `mut`, tipo e inicializador (T4); `const` local; `=`, `+=`, `-=`, `*=`, `/=` sobre variables, campos y elementos; `if` / `else if` / `else`; `while`; `loop`; `break`; `continue`; `return`; bloques.
- Expresiones: `+ - * / %`, comparaciones, `&& ||` con cortocircuito, `-x`, `!x`, `&x`, `&mut x`, `*r`, llamadas, campos, índices (con auto-deref de un nivel), literales de struct, enum, tupla y array, `match` como expresión y bloques como expresión (T5).
- Patrones: `_`, literales `i32`/`f64`/`bool`/`char`, identificadores, variantes de enum con subpatrones anidados (G10) y tuplas.

**Semántica**

- Ámbitos léxicos, declaración antes de uso y sombreado solo en ámbitos internos (G2).
- Inferencia de tipos de locales desde el inicializador.
- Tipos de operadores, condiciones, asignaciones, argumentos (número y tipo), retornos en todos los caminos (incluidos `match` con `return` en todos los brazos), campos de structs y datos de variantes.
- `match`: tipos compatibles entre brazos y exhaustividad (G10, G11).
- Mutabilidad de variables, campos, elementos y `&mut`.
- Ownership: movimientos de valores no Copy (G1), uso después de mover, ramas y ciclos (G8), partes de un valor (G12) y variables sin inicializar (T4).
- Borrowing: varios `&` o un solo `&mut`, sin usar al dueño mientras hay un `&mut` (G9), sin asignar ni mover algo prestado, sin devolver referencias a locales (`E_RETURN_LOCAL_REF`) y sin referencias colgantes (`E_DANGLING_REF`).
- Errores léxicos, sintácticos y semánticos con fase, código, línea, columna y largo (T6).

**Generación de código**

- WAT con todas las construcciones anteriores, convertido con `wat2wasm` y validado con `wasm-validate`. Si hay un solo error no se produce módulo.
- Representación en memoria de `String`, arrays, tuplas, structs, enums y referencias en `memoria.md`.
- Ejecución con wasmtime (pruebas) y con la API de WebAssembly del navegador (editor). Salida con `print_i32`, `print_f64`, `print_bool`, `print_char` y `print_str` (P1).
- Índice fuera de rango: error de compilación si es literal, trap al ejecutar si es calculado.

## Parcial

- Préstamos: duran hasta el fin del bloque de la variable que los guarda, no hasta su último uso (G9).
- Movimientos parciales: mover un campo deja movida toda la variable (G12).
- Ramas y ciclos: reponer una variable dentro de una rama no cuenta, y mover dentro de un ciclo algo declarado fuera es error aunque venga `break` (G8).
- Exhaustividad: con patrones anidados refutables hace falta un brazo `_` (G10). Los brazos repetidos o inalcanzables no se reportan (G11).
- `match` sobre una referencia a enum: se usa `match *e { ... }`. Los patrones de variante sobre `&E` no se aceptan.
- `String`: crear, mover, pasar, retornar e imprimir. Sin concatenación ni comparación (P9).
- Memoria: el heap nunca se libera (G3).
- Constantes: no se verifica que el inicializador sea constante ni que no sea recursivo (G6).

## No soportado

Ninguna de estas construcciones está en la EBNF del profesor, salvo donde se indica.

- `if` como expresión (P4), `t.0` (P2), `*r = valor` (P3), patrones negativos (P6) y conversiones `as` (P8).
- `for` y rangos, `%=`, `break` con valor, etiquetas de ciclo y `[x; n]`.
- Varios prefijos unarios seguidos: `- -x`, `!!x`, `**r`, `&&x` como expresión (T3). Comparaciones encadenadas `a < b < c` (T2).
- `%` con `f64`. Está en la EBNF, pero Wasm no tiene resto de `f64`.
- `==` entre `String`, structs, tuplas, arrays o referencias, y `<` entre `bool`.
- Literales `1e5`, `1.`, `.5`, `0x10` y `1_000`; escapes `\0` y `\u{...}`; comentarios de bloque anidados; identificadores con letras fuera de ASCII.
- Métodos (`impl`), traits, genéricos, closures, módulos, `Vec` y `Option`.

## Diferencias con Rust

- Los arrays y las tuplas siempre se mueven (G1). En Rust son Copy si todos sus elementos lo son.
- Una variable movida dentro de una rama no se repone aunque se le asigne un valor nuevo en esa misma rama (G8). Rust sí la repone si se reasigna en todos los caminos.
- Un préstamo guardado en una variable vive hasta el fin del bloque de esa variable, aunque ya no se use (G9). Rust lo termina en su último uso.
- Un `match` con patrones anidados refutables necesita un brazo `_` (G10). Rust calcula la exhaustividad exacta.
- RustiQ no tiene el tipo `!` de Rust. Un brazo de `match` cuyo bloque termina en `return`, `break` o `continue` no fija el tipo del `match`, y un `match` con `return` en todos los brazos cuenta como camino que termina la función.
- Rust avisa de brazos inalcanzables en un `match`; RustiQ no.
- Mover dentro de un ciclo una variable declarada fuera es error aunque después venga `break` o `return` (G8). Rust lo permite si el ciclo no vuelve a usarla.
- No hay liberación de memoria (`drop`).
- `+`, `-` y `*` sobre `i32` dan la vuelta al desbordarse (aritmética de Wasm); Rust en modo debug entra en pánico. Dividir entre cero o `-2147483648 / -1` sí hacen trap.
- `print_f64` imprime con el formato de Python (G13): `3.0`, `1e-05`. Rust imprime `3` y `0.00001`.
- No hay movimientos parciales: `let n = p.nombre;` deja movida toda la variable `p` (G12). Rust solo marca movido ese campo y deja usar los demás.
