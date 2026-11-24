# Decisiones del lenguaje

Qué se soporta, qué no, y en qué se diferencia RustiQ de Rust.

## Ajustes técnicos de ANTLR

| # | Tema | Decisión |
| --- | --- | --- |
| T1 | Struct literal contra bloque | Prohibido suelto en condiciones de `if`, `while` y en el valor de `match`. Se permite entre paréntesis, corchetes, llaves o como argumento de una llamada (`if suma(Punto { x: 1, y: 2 }) == 3`) |
| T2 | Comparaciones encadenadas | `a < b < c` es error sintáctico, igual que en Rust |
| T3 | `&&x` | No soportado. `unary` acepta un solo prefijo, así que la gramática tampoco permite `& &x` |
| T4 | `let` sin inicializador | Válido si el tipo se indica y se asigna antes de usarse. Cuenta como asignada si se le asigna en todas las ramas de un `if` con `else` o de un `match` Reutiliza el estado "sin inicializar" de movimientos |
| T5 | Bloque anidado como valor final | ANTLR lee `{ { 3 } }` con el bloque interno como sentencia. Si la última sentencia de un bloque es otro bloque que produce valor y no hay otra expresión final, ese bloque es la expresión final (`flow.block_tail`) |
| T6 | Errores léxicos | El lexer tiene tokens de error en el canal oculto (`BAD_STRING`, `UNTERMINATED_STRING`, `BAD_CHAR`, `UNTERMINATED_CHAR`, `UNTERMINATED_COMMENT`). El parser no los ve y el pipeline los reporta como `E_UNTERMINATED_STRING`, `E_INVALID_ESCAPE`, `E_UNTERMINATED_COMMENT` o `E_INVALID_CHAR`, con la posición exacta |
| T7 | Anidación máxima | Un programa con más de 256 niveles de `(`, `{` y `[` abiertos a la vez es error `E_TOO_NESTED` y no se parsea. Se cuenta sobre los tokens, así que no cuentan los que están dentro de strings o comentarios. El parser usa predicción SLL: con LL completo, los bloques anidados tardan tiempo superlineal |

## Soportado

**Léxico y sintaxis** (ANTLR4, `grammar/RustiQ.g4`)

- Comentarios `//` y `/* */`. Literales `i32` (decimal), `f64` (`1.5`), `bool`, `char` y `String` con los escapes `\n \t \r \\ \" \'`, y Unicode dentro de `char` y `String`.
- Items: `fn`, `struct`, `enum` (variantes sin datos o con datos) y `const` global. Se pueden declarar en cualquier orden.
- Tipos: `i32`, `f64`, `bool`, `char`, `String`, arrays `[T; N]`, tuplas, `&T`, `&mut T`, `&&T`, structs y enums.
- Sentencias: `let` con o sin `mut`, tipo e inicializador (T4); `const` local; `=`, `+=`, `-=`, `*=`, `/=` sobre variables, campos y elementos; `if` / `else if` / `else`; `while`; `loop`; `break`; `continue`; `return`; bloques.
- Expresiones: `+ - * / %`, comparaciones, `&& ||` con cortocircuito, `-x`, `!x`, `&x`, `&mut x`, `*r`, llamadas, campos, índices (con auto-deref de un nivel), literales de struct, enum, tupla y array, `match` como expresión y bloques como expresión (T5).
- Patrones: `_`, literales `i32`/`f64`/`bool`/`char`, identificadores, variantes de enum con subpatrones anidados y tuplas.

**Semántica**

- Ámbitos léxicos, declaración antes de uso y sombreado solo en ámbitos internos.
- `main` es obligatoria, sin parámetros y sin valor de retorno (`E_BAD_MAIN`).
- Inferencia de tipos de locales desde el inicializador.
- Tipos de operadores, condiciones, asignaciones, argumentos (número y tipo), retornos en todos los caminos (incluidos `match` con `return` en todos los brazos), campos de structs y datos de variantes.
- `match`: tipos compatibles entre brazos y exhaustividad.
- Mutabilidad de variables, campos, elementos y `&mut`.
- Tipos Copy: solo `i32`, `f64`, `bool`, `char`, `()` y `&T`. Todo lo demás se mueve: `String`, arrays, tuplas, structs, enums y `&mut T`.
- Ownership: movimientos de valores no Copy, uso después de mover, ramas y ciclos, partes de un valor y variables sin inicializar (T4).
- Borrowing: varios `&` o un solo `&mut`, sin usar al dueño mientras hay un `&mut`, sin asignar ni mover algo prestado, sin devolver referencias a locales (`E_RETURN_LOCAL_REF`) y sin referencias colgantes (`E_DANGLING_REF`).
- Errores léxicos, sintácticos y semánticos con fase, código, línea, columna y largo (T6).

**Generación de código**

- WAT con todas las construcciones anteriores, convertido con `wat2wasm` y validado con `wasm-validate`. Si hay un solo error no se produce módulo.
- Representación en memoria de `String`, arrays, tuplas, structs, enums y referencias en `memoria.md`.
- Ejecución con wasmtime (pruebas) y con la API de WebAssembly del navegador (editor). Salida con `print_i32`, `print_f64`, `print_bool`, `print_char` y `print_str`. Cada llamada imprime una línea, y imprimir no mueve el valor.
- Índice fuera de rango: error de compilación si es literal, trap al ejecutar si es calculado.

## Parcial

- Préstamos: duran hasta el fin del bloque de la variable que los guarda, no hasta su último uso.
- Movimientos parciales: mover un campo deja movida toda la variable.
- Ramas y ciclos: reponer una variable dentro de una rama no cuenta, y mover dentro de un ciclo algo declarado fuera es error aunque venga `break`.
- Exhaustividad: con patrones anidados refutables hace falta un brazo `_`. Los brazos repetidos o inalcanzables no se reportan.
- `match` sobre una referencia a enum: se usa `match *e { ... }`. Los patrones de variante sobre `&E` no se aceptan.
- `String`: crear, mover, pasar, retornar e imprimir. Sin concatenación ni comparación.
- Memoria: el heap nunca se libera.
- Constantes: no se verifica que el inicializador sea constante ni que no sea recursivo.

## No soportado

Ninguna de estas construcciones está en la gramática de RustiQ, salvo donde se indica.

- `if` como expresión, `t.0`, `*r = valor`, patrones negativos y conversiones `as`.
- `for` y rangos, `%=`, `break` con valor, etiquetas de ciclo y `[x; n]`.
- Varios prefijos unarios seguidos: `- -x`, `!!x`, `**r`, `&&x` como expresión (T3). Comparaciones encadenadas `a < b < c` (T2).
- `%` con `f64`. Está en la gramática, pero Wasm no tiene resto de `f64`.
- `==` entre `String`, structs, tuplas, arrays o referencias, y `<` entre `bool`.
- Literales `1e5`, `1.`, `.5`, `0x10` y `1_000`; escapes `\0` y `\u{...}`; comentarios de bloque anidados; identificadores con letras fuera de ASCII.
- Métodos (`impl`), traits, genéricos, closures, módulos, `Vec` y `Option`.

## Diferencias con Rust

- Los arrays y las tuplas siempre se mueven. En Rust son Copy si todos sus elementos lo son.
- Una variable movida dentro de una rama no se repone aunque se le asigne un valor nuevo en esa misma rama. Rust sí la repone si se reasigna en todos los caminos.
- Un préstamo guardado en una variable vive hasta el fin del bloque de esa variable, aunque ya no se use. Rust lo termina en su último uso.
- Un `match` con patrones anidados refutables necesita un brazo `_`. Rust calcula la exhaustividad exacta.
- RustiQ no tiene el tipo `!` de Rust. Un brazo de `match` cuyo bloque termina en `return`, `break` o `continue` no fija el tipo del `match`, y un `match` con `return` en todos los brazos cuenta como camino que termina la función.
- Rust avisa de brazos inalcanzables en un `match`; RustiQ no.
- Mover dentro de un ciclo una variable declarada fuera es error aunque después venga `break` o `return`. Rust lo permite si el ciclo no vuelve a usarla.
- No hay liberación de memoria (`drop`).
- `+`, `-` y `*` sobre `i32` dan la vuelta al desbordarse (aritmética de Wasm); Rust en modo debug entra en pánico. Dividir entre cero o `-2147483648 / -1` sí hacen trap.
- `print_f64` imprime con el formato de Python: `3.0`, notación científica si el exponente es menor que -4 o al menos 16 (`1e-05`, `1e+16`), e `inf`, `-inf` y `nan`. Rust imprime `3` y `0.00001`.
- No hay movimientos parciales: `let n = p.nombre;` deja movida toda la variable `p`. Rust solo marca movido ese campo y deja usar los demás.
