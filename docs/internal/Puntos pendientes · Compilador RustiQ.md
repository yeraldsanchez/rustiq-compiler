# Puntos pendientes · Compilador RustiQ

Nov 3, 2026 · @Yerald Sanchez

Mientras un punto no se resuelva, el plan usa la opción por defecto indicada en cada uno. Conviene cerrar los de gramática antes del jueves 12 de noviembre, porque después afectan tipos y codegen al mismo tiempo.

## Respuesta del profesor

Nov 9, 2026.

- Acepta las funciones `print_*` para la salida (P1).
- Que la gramática sea más restrictiva que Rust no es un problema: la idea es justamente que RustiQ sea diferente de Rust. La gramática se sigue tal como está.
- Solo se puede agregar algo que no esté en la gramática si se justifica que, sin eso, otra parte de la gramática no funcionaría.

Con eso P2, P3, P4, P5, P6, P8 y P9 quedan con la opción por defecto, apegada a la gramática. P7 y P10 se deciden en el grupo usando el mismo criterio.

## Tablero

| # | Punto | Consultar con | Opción por defecto | Estado | Decisión final |
| --- | --- | --- | --- | --- | --- |
| P1 | Funciones de salida `print_*` | Profesor | Usarlas | Resuelto | Se usan las funciones `print_*` |
| P2 | Acceso a tuplas con `t.0` | Profesor | No existe, solo match | Resuelto | No existe, las tuplas se leen con match |
| P3 | Asignar con `*r = valor` | Profesor | No existe | Resuelto | No existe |
| P4 | `if` como expresión | Profesor | Solo sentencia | Resuelto | Solo sentencia |
| P5 | `match` sin `;` en medio de un bloque | Profesor | Exigir `;` | Resuelto | Se exige `;` |
| P6 | Patrones con números negativos | Profesor | No permitidos | Resuelto | No permitidos |
| P7 | Identificadores que empiezan con `_` | Grupo | Seguir las reglas léxicas: pueden empezar con letra o `_` | Resuelto | Pueden empezar con letra o `_`. `_` solo es el comodín |
| P8 | Conversión entre i32 y f64 | Profesor | No existe | Resuelto | No existe |
| P9 | Operaciones sobre String | Profesor | Crear, mover, pasar, imprimir | Resuelto | Crear, mover, pasar, retornar e imprimir. Sin concatenación ni comparación |
| P10 | Tipo `&&T` escrito sin espacio | Grupo | No soportado, se escribe `& &T` | Resuelto | Soportado en tipos. `&&x` en expresiones no existe |
| G1 | Qué tipos son Copy | Grupo | Regla de Rust | Resuelto | Solo escalares, `()` y `&T`. Arrays, tuplas, String, structs y enums se mueven |
| G2 | Sombreado en el mismo ámbito | Grupo | Prohibido, solo en ámbitos internos | Resuelto | Prohibido en el mismo ámbito, permitido en ámbitos internos |
| G3 | Manejo de memoria | Grupo | Bump allocator sin liberar | Resuelto | Bump allocator sin liberar, con `memory.grow` |

## Puntos para el profesor

### P1 · Funciones de salida

**De dónde sale:** el enunciado pide un panel de salida del programa ejecutado. La gramática no tiene `println!` porque deja fuera las macros.

**Problema:** sin una forma de imprimir, la única salida posible es el valor que retorna `main`.

**Propuesta:** funciones builtin que el módulo Wasm importa desde el host. Se llaman como funciones normales, así que no cambian la gramática.

```rust
fn main() {
    print_i32(42);
    print_f64(3.5);
    print_str("hola");
}
```

**Pregunta:** ¿acepta estas funciones builtin, o espera otra forma de mostrar resultados?

**Respuesta:** las acepta.

### P2 · Acceso a elementos de tupla

**De dónde sale:** `fieldSuffix = "." identifier`. Después del punto solo cabe un identificador, no un número.

**Problema:** una tupla se puede crear pero no leer por posición.

```rust
let d: (f64, f64) = (1.0, 2.0);
let a = d.0;                       // inválido con la EBNF

let a = match d { (x, _) => x };   // única forma válida
```

**Detalle técnico si se agrega:** el lexer lee `d.0.1` como `d`, `.` y el float `0.1`. Hay que manejarlo.

**Pregunta:** ¿agregamos `t.0` o las tuplas solo se leen con match?

**Respuesta:** se sigue la gramática. Las tuplas solo se leen con match.

### P3 · Asignar a través de una referencia

**De dónde sale:** `place = identifier { "." identifier | "[" expression "]" }`. No incluye `*`.

**Problema:** `*r` se puede leer porque `unary` acepta `*`, pero no se puede asignar.

```rust
fn inc(r: &mut i32) {
    *r = *r + 1;     // inválido: *r no es un place
}

fn mover_x(p: &mut Punto, dx: f64) {
    p.x = p.x + dx;  // válido: el ejemplo oficial lo usa
}
```

Con esto `&mut` solo sirve para structs y arrays, no para escalares.

**Pregunta:** ¿agregamos `*` al place?

**Respuesta:** se sigue la gramática. `*r = valor` no existe.

### P4 · `if` como expresión

**De dónde sale:** `ifStmt` aparece en `statement`. En `primary` están `matchExpr` y `block`, pero no `if`.

**Problema:** `match` y los bloques producen valor, `if` no.

```rust
let x = match c { true => 1, false => 2 };   // válido
let x = if c { 1 } else { 2 };               // inválido con la EBNF
```

**Pregunta:** ¿`if` debe poder usarse como expresión?

**Respuesta:** se sigue la gramática. `if` es solo sentencia.

### P5 · `match` como sentencia sin punto y coma

**De dónde sale:** `statement` incluye `expression ";"`. Como `match` es expresión, en medio de un bloque exige `;`.

**Problema:** en Rust el `;` se omite después de expresiones que terminan en llave.

```rust
fn main() {
    match e {
        Estado::Pendiente => print_i32(0),
        _ => print_i32(1),
    }                 // sin ; da error sintáctico con la EBNF
    let y = 3;
}
```

**Pregunta:** ¿se exige `;` o se permite omitirlo como en Rust?

**Respuesta:** se sigue la gramática. Se exige `;`.

### P6 · Patrones con números negativos

**De dónde sale:** `pattern` usa `literal`, y `integerLiteral = digit { digit }` no tiene signo. El signo es un operador unario de expresiones.

```rust
match codigo {
    -1 => print_str("error"),   // inválido con la EBNF
    0 => print_str("ok"),
    _ => print_str("otro"),
}
```

**Pregunta:** ¿se permiten patrones negativos?

**Respuesta:** se sigue la gramática. No se permiten.

### P7 · Identificadores con guion bajo inicial

**De dónde sale:** la EBNF dice `identifier = letter { letter | digit | "_" }`. Las reglas léxicas dicen que empiezan con letra o guion bajo. Se contradicen.

```rust
let _temp = 5;    // válido según las notas, inválido según la EBNF
match x { _ => 0 }  // _ solo siempre es comodín
```

**Detalle técnico si se permite:** `_` solo tiene que ser un token aparte para que no se confunda con un identificador.

**Pregunta:** ¿cuál de las dos reglas vale?

**Decisión del grupo:** seguir las reglas léxicas, que es lo que ya hace el lexer (`[a-zA-Z_] [a-zA-Z0-9_]*`). Un identificador puede empezar con letra o `_`, así que `_temp` es válido. `_` solo sigue siendo el comodín porque el token `UNDERSCORE` está definido antes que `IDENT`. No requiere cambios en el código.

### P8 · Conversión entre i32 y f64

**De dónde sale:** no existe `as` ni ninguna función de conversión. Los dos tipos numéricos quedan aislados.

```rust
let n: i32 = 3;
let x: f64 = n * 1.5;       // error de tipos
let x: f64 = n as f64;      // as no existe
```

**Pregunta:** ¿se deja así, o se agrega `as` o un builtin como `to_f64`?

**Respuesta:** se sigue la gramática. No hay conversión.

### P9 · Operaciones sobre String

**De dónde sale:** la gramática incluye el tipo `String` y literales de cadena. No define ningún operador ni método sobre ellos. Tampoco existe `str`.

**Problema:** no está claro qué se espera hacer con un String más allá de crearlo y moverlo.

```rust
let a = "hola";
let b = a;               // move, claro
let c = a + " mundo";    // ¿válido?
let d = b == "hola";     // ¿válido?
```

**Pregunta:** ¿basta con crear, mover, pasar, retornar e imprimir, o espera concatenación y comparación?

**Respuesta:** se sigue la gramática. Crear, mover, pasar, retornar e imprimir. Sin concatenación ni comparación.

### P10 · Tipo referencia a referencia `&&T`

**De dónde sale:** `referenceType = "&" [ "mut" ] type`. Como `type` puede ser otra referencia, la EBNF acepta `&&i32` y `&&mut i32`.

**Problema:** el lexer toma siempre el token más largo, así que `&&` se lee como el operador lógico `AND` y no como dos `&`. Con el `.g4` actual:

```rust
fn f(r: & &i32) {}    // válido: dos tokens &
fn f(r: &&i32) {}     // error sintáctico, aunque la EBNF lo permite
```

Es el mismo problema que T3 tiene en expresiones (`&&x`).

**Detalle técnico si se soporta:** agregar a `type` la alternativa `"&&" [ "mut" ] type`, que se lee como `& (& [mut] T)`, y regenerar el parser. No cambia el lexer.

**Pregunta:** ¿hace falta soportar `&&T` sin espacio, o basta con documentarlo como no soportado?

**Decisión del grupo:** se soporta en tipos. La EBNF ya permite `&&i32` porque `referenceType` es recursivo, así que no se agrega nada nuevo: solo se hace que el parser acepte lo que la gramática ya dice, lo que cumple el criterio del profesor. Se agregó la alternativa `AND MUT? type` (`RefRefT`) a `type`, que equivale a `& (& [mut] T)`.

En expresiones es distinto: `unary` acepta un solo prefijo, así que `&&x` ni `& &x` son válidos según la EBNF. Un valor de tipo `&&T` se crea pasando por una variable (`let r = &x; let rr = &r;`) y se lee con `*(*rr)`.

## Decisiones del grupo

El enunciado deja estas decisiones abiertas. Se pueden tomar sin consultar, siempre que se documenten y se expliquen en la defensa.

**Criterio del grupo (16 de noviembre de 2026):** se elige la opción más sencilla que cumpla el enunciado. G2 y G3 quedan con su opción por defecto. G1 se simplifica: arrays y tuplas también se mueven, así ninguna copia necesita `memcpy`. La decisión final de cada una está en `docs/decisiones.md`.

### G1 · Qué tipos son Copy

**De dónde sale:** el enunciado dice "los valores no copiables se mueven al transferir su propiedad". Nunca dice cuáles son copiables.

**Por qué importa:** decide qué asignaciones y llamadas mueven la variable de origen. Es la base de todo el análisis de ownership.

**Opción por defecto, la regla de Rust:**

| Tipo | ¿Copy? | Razón |
| --- | --- | --- |
| i32, f64, bool, char | Sí | Primitivos, caben en un registro |
| `&T` | Sí | Varias referencias inmutables pueden coexistir |
| `&mut T` | No | Debe ser exclusiva |
| Array o tupla | Solo si todos sus elementos son Copy | Igual que Rust |
| String | No | Es dueño de memoria en el heap |
| Struct, enum | No | En Rust necesitan `#[derive(Copy)]`, y RustiQ no tiene atributos |

```rust
let a = 5;
let b = a;
print_i32(a);          // válido: i32 es Copy

let s = "hola";
let t = s;
print_str(s);          // error: s fue movida a t

let e = Estado::Pendiente;
describir(e);
describir(e);          // error: e se movió en la primera llamada
```

El ejemplo oficial de la gramática confirma que los enums se mueven: dice que `describir(estado)` mueve la propiedad.

### G2 · Sombreado

**De dónde sale:** el enunciado dice que no se puede "declarar dos veces el mismo nombre en un mismo ámbito, salvo reglas de sombreado que el grupo defina y documente".

**Qué significa:** la regla base lo prohíbe. La frase final permite que el grupo defina sombreado si lo documenta. No está prohibido del todo.

```rust
fn main() {
    let x = 5;
    let x = x + 1;      // mismo ámbito: opción A error, opción B válido
    {
        let x = 10;     // ámbito interno: válido en ambas opciones
        print_i32(x);   // 10
    }
    print_i32(x);       // 6 con opción B
}
```

**Opciones:**

- **A, por defecto:** prohibido en el mismo ámbito, permitido en ámbitos internos. Sigue la regla base del enunciado sin excepciones.
- **B:** permitido como en Rust. Hay que documentarlo como regla de sombreado propia.

Para la implementación da casi igual. El `uid` de cada símbolo ya distingue variables con el mismo nombre.

### G3 · Manejo de memoria

**De dónde sale:** el enunciado pide "definir y documentar la representación en memoria de String, arrays, tuplas, structs, enums y referencias".

**Por qué hay que decidir:** Wasm solo maneja números: i32, i64, f32, f64. Todo valor compuesto vive en la memoria lineal, un arreglo grande de bytes. El compilador decide cómo se reparte y quién pide espacio.

**Opciones:**

| Opción | Cómo funciona | Costo | Riesgo |
| --- | --- | --- | --- |
| Bump allocator, por defecto | Un puntero que solo avanza. Pedir memoria es sumar | Unas 10 líneas de WAT | Nunca libera. Un loop que crea muchos String puede llenar la memoria |
| Free list | Lista de bloques libres que se reutilizan | Implementar el drop de Rust: liberar al salir del ámbito | Mucho trabajo y bugs difíciles de rastrear |
| Wasm GC | El runtime administra la memoria | Otro modelo de tipos en el backend | Soporte desigual entre runtimes |

```wat
(global $heap (mut i32) (i32.const 1024))
(func $alloc (param $n i32) (result i32)
  (local $p i32)
  (local.set $p (global.get $heap))
  (global.set $heap (i32.add (global.get $heap) (local.get $n)))
  (local.get $p))
```

Con `memory.grow` el riesgo del bump se reduce mucho para programas de prueba.

### G4 · Alcance de String

Resuelto con P9: se sigue la gramática. Literal, move, pasar como argumento, retornar e imprimir. Concatenar con `+` requiere pedir memoria nueva y copiar bytes. Comparar con `==` requiere recorrer ambos strings. Los dos son trabajo extra de B en la etapa 3.

## Ajustes técnicos de ANTLR

No cambian el lenguaje. El documento de gramática ya avisa que la EBNF "es una especificación conceptual" y que en ANTLR hay que adaptar prefijos de expresiones, bloques y la ambigüedad entre structLiteral y bloques. Se documentan, pero no hace falta preguntarlos.

### T1 · Struct literal contra bloque

**De dónde sale:** `structLiteral = identifier "{" ...` y `ifStmt = "if" expression block`. Las dos empiezan con identificador seguido de `{`.

```rust
if listo { p.x = 1.0; }
// ¿es la condición listo seguida de un bloque,
// o un struct literal listo { ... } sin bloque después?
```

**Solución:** la misma de Rust. Una regla de expresión sin struct literal para la condición de `if` y `while` y para el valor de `match`. Si alguien necesita un struct ahí, lo pone entre paréntesis.

```rust
if p == (Punto { x: 1.0, y: 2.0 }) { ... }   // con paréntesis, válido
```

### T2 · Comparaciones encadenadas

**De dónde sale:** `comparison = additive [ relOp additive ]`. Los corchetes permiten una sola comparación.

```rust
let a = x < y;          // válido
let b = x < y < z;      // error sintáctico
let c = (x < y) == ok;  // válido con paréntesis
```

**Solución:** respetarlo en ANTLR. Rust hace lo mismo, así que no es una diferencia que haya que explicar.

### T3 · `&&` en posición unaria

**De dónde sale:** el lexer toma siempre el token más largo. `&&x` se lee como el operador lógico `&&` seguido de `x`, no como dos `&`.

```rust
let r = &&x;    // referencia a una referencia
```

**Solución:** no se soporta. `unary` acepta un solo prefijo, así que la EBNF tampoco permite `& &x`. El error sintáctico coincide con la gramática. El caso de tipos (`&&i32`) sí está en la EBNF y se resolvió en P10.

### T4 · `let` sin inicializador

**De dónde sale:** `letDecl = "let" [ "mut" ] identifier [ ":" type ] [ "=" expression ] ";"`. El inicializador es opcional.

```rust
let x: i32;
if c { x = 1; } else { x = 2; }
print_i32(x);    // válido: ambas ramas asignan

let y: i32;
print_i32(y);    // error: y sin inicializar
```

**Solución:** el análisis de ownership ya tiene el estado "sin inicializar". Se reutiliza. Un `let` sin tipo ni inicializador es error porque no se puede inferir el tipo.
