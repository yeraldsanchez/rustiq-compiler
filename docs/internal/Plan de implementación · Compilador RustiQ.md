# Plan de implementación · Compilador RustiQ

Nov 3, 2026 · @Yerald Sanchez

## Resumen

Código congelado el viernes 20 de noviembre. Entrega el domingo 22 antes de las 10:00 pm. Son 5 etapas en 19 días.

El trabajo se divide por características, no por fases. Cada uno implementa sus características completas: gramática, tipos, generación de código y pruebas. Así ambos tocan todo el compilador y pueden defenderlo.

- **Persona A:** en la gramática, items, tipos y patrones. Características: funciones, control de flujo, constantes, structs, tuplas, enums, match y movimientos. Infraestructura: pipeline, runtime, layout de memoria y servidor FastAPI.
- **Persona B:** en la gramática, léxico, expresiones y sentencias. Características: ámbitos, operadores, inferencia, mutabilidad, arrays, Strings, referencias y préstamos. Infraestructura: error listener, editor y los dos hosts de salida.

Lo que evita choques son los contratos de la etapa 0. Cada carril trabaja contra una interfaz fija, no contra el código del otro. Si un contrato cambia, se avisa y se actualiza en el mismo PR.

Ambos revisan los PR del otro. La defensa exige que los dos expliquen todo el compilador, y la revisión cruzada es la forma de lograrlo sin tiempo extra.

Los puntos sin resolver están en un documento aparte. El plan asume la gramática EBNF tal cual, y cada punto pendiente es una extensión aislada que se puede agregar después.

## Stack y herramientas

Versiones fijadas en `requirements.txt` para que ambas máquinas y CI den el mismo resultado.

| Pieza                   | Herramienta                                                        | Uso                                                                          |
|-------------------------|--------------------------------------------------------------------|------------------------------------------------------------------------------|
| Lenguaje                | Python 3.11 o superior                                             | Todo el compilador                                                           |
| Parser                  | ANTLR4 4.13.2 con `antlr4-tools` y `antlr4-python3-runtime` 4.13.2 | Lexer y parser con destino Python. Herramienta y runtime en la misma versión |
| Salida del backend      | WAT generado como texto desde Python                               | Legible y fácil de mostrar en la defensa                                     |
| Conversión y validación | wabt: `wat2wasm` y `wasm-validate`                                 | Evidencia oficial de módulo válido                                           |
| Respaldo de conversión  | `wasmtime.wat2wasm`                                                | Si wabt falla en alguna máquina                                              |
| Runtime de pruebas      | `wasmtime` para Python                                             | Ejecuta los .wasm dentro de pytest y en CI                                   |
| Runtime del editor      | API `WebAssembly` del navegador                                    | Ejecuta el módulo recién compilado                                           |
| Servidor                | FastAPI con uvicorn                                                | Endpoint de compilación                                                      |
| Editor                  | CodeMirror 6                                                       | Números de línea, resaltado y marcas de error                                |
| Pruebas                 | pytest                                                             | Regresión válida e inválida                                                  |
| CI                      | GitHub Actions                                                     | Corre pytest en cada push                                                    |

Los archivos generados por ANTLR se suben al repo. Así nadie necesita Java para compilar, solo para regenerar la gramática.

## Estructura del repositorio y flujo Git

Cada archivo tiene un dueño. La única excepción es el `.g4`, donde cada uno llena sus reglas sobre un esqueleto común escrito en la etapa 0.

```
rustiq/
  grammar/RustiQ.g4              A items, tipos, patrones · B léxico, expresiones, sentencias
  rustiq/
    generated/                   salida de ANTLR, no se edita a mano
    errors.py                    contrato
    types.py                     contrato
    syntax_errors.py             B  error listener
    host.py                      B  print_* para wasmtime
    semantic/
      info.py                    contrato  SemanticInfo
      analyzer.py                contrato  visitor principal con mixins
      scopes.py                  B
      check_exprs.py             B  literales, operadores, inferencia, mutabilidad
      check_arrays.py            B
      check_refs.py              B  referencias y Strings
      borrows.py                 B
      check_items.py             A  funciones, constantes, structs, tuplas
      check_control.py           A
      check_match.py             A  enums y match
      moves.py                   A
    codegen/
      emitter.py                 A  base: módulo, funciones, locales, mixins
      gen_control.py             A
      gen_structs.py             A  structs y tuplas
      gen_match.py               A  enums y match
      gen_exprs.py               B
      gen_arrays.py              B
      gen_refs.py                B  referencias y Strings
      runtime.wat                A  allocator y helpers
    pipeline.py                  A  parse, semántica, codegen, wat2wasm, validate
    cli.py                       A
  server/app.py                  A
  web/
    index.html, editor.js        B
    host.js                      B  print_* del navegador
  tests/
    valid/    *.rq y *.out       ambos
    invalid/  *.rq               ambos
    test_suite.py                A
  docs/
    decisiones.md                ambos
    memoria.md                   A
  scripts/gen_grammar.sh         B
```

Flujo:

- `main` siempre pasa CI. Nadie empuja directo a `main`.
- Una rama por tarea: `a/typecheck-structs`, `b/codegen-match`.
- PR pequeños, de uno o dos días de trabajo. El otro revisa y aprueba.
- Un cambio a un archivo marcado como contrato va en su propio PR, primero, y se avisa por chat.
- Cada PR agrega al menos un programa de prueba.

## Contratos entre módulos

Se escriben juntos en la etapa 0, antes de dividirse. Son siete. Con ellos cada uno avanza en sus características sin esperar el código del otro.

### 1. Errores · `errors.py`

Todas las fases reportan igual. El editor y las pruebas dependen de este formato.

```python
@dataclass
class CompileError:
    phase: str      # "lexico" | "sintactico" | "semantico" | "backend"
    code: str       # "E_UNDECLARED", "E_TYPE_MISMATCH", "E_USE_AFTER_MOVE", ...
    message: str    # en español
    line: int       # desde 1
    column: int     # desde 1. ANTLR da columnas desde 0, se suma 1
    length: int = 1 # para subrayar en el editor
```

La lista de códigos vive en el mismo archivo. Agregar un código no rompe nada.

### 2. Tipos · `types.py`

```python
I32, F64, BOOL, CHAR, STRING, UNIT          # singletons
ArrayT(elem: Type, size: int)
TupleT(elems: tuple[Type, ...])
RefT(target: Type, mutable: bool)
StructT(name: str)
EnumT(name: str)

def is_copy(t: Type) -> bool               # regla única, la usan A y B
```

### 3. Resultado semántico · `semantic/info.py`

Es la frontera entre A y B. El codegen lee solo esto y nunca vuelve a inferir tipos. Se usa `ParseTreeProperty` de ANTLR para anotar el árbol sin construir un AST.

```python
class SemanticInfo:
    expr_type: ParseTreeProperty     # ctx de expresión -> Type
    symbol: ParseTreeProperty        # ctx de identificador -> Symbol
    structs: dict[str, StructDef]    # campos en orden de declaración
    enums: dict[str, EnumDef]        # variantes con tag 0, 1, 2...
    functions: dict[str, FuncSig]

@dataclass
class Symbol:
    uid: int          # único en todo el programa, resuelve sombreado
    name: str
    type: Type
    mutable: bool
    kind: str         # "local" | "param" | "const" | "func"
    address_taken: bool  # True si se le aplica & y es escalar
```

### 4. ABI del módulo Wasm

- Exporta `memory` y `main`.
- Importa desde `env`: `print_i32`, `print_f64`, `print_bool`, `print_char`, `print_str`. Pendiente de aprobación del profesor.
- El host se implementa dos veces con el mismo comportamiento: en Python para pytest y en `host.js` para el navegador.

### 5. Representación en memoria · `docs/memoria.md`

Propuesta inicial. A la puede ajustar, pero se documenta antes de cambiarla.

| Tipo                     | Representación en Wasm                                         |
|--------------------------|----------------------------------------------------------------|
| i32, bool, char          | `i32` en local                                                 |
| f64                      | `f64` en local                                                 |
| String                   | puntero a `[len: i32][bytes UTF-8]`                            |
| Struct, tupla            | puntero a campos en orden, cada uno en una ranura de 8 bytes   |
| Array                    | puntero a `n` ranuras de 8 bytes                               |
| Enum                     | puntero a `[tag: i32][relleno][payload en ranuras de 8 bytes]` |
| Referencia               | `i32` con la dirección                                         |
| Escalar con `&` aplicado | vive en una celda del heap, el local guarda su dirección       |

Heap con bump allocator desde la dirección 1024. Un global `$heap` que solo avanza y usa `memory.grow` si se acaba.

### 6. API del servidor

```
POST /compile
  { "source": "..." }
→ { "ok": true,  "errors": [], "wat": "...", "wasm_base64": "..." }
→ { "ok": false, "errors": [CompileError...], "wat": null, "wasm_base64": null }
```

Si hay un solo error, nunca se devuelve wasm. Así lo exige el enunciado.

### 7. Esqueleto de gramática y visitors

Es lo que permite que dos personas trabajen en los mismos componentes sin pisarse.

- El `.g4` se escribe en la etapa 0 con todas las reglas declaradas y un comentario con su dueño. Cada uno llena solo las suyas.
- `semantic/analyzer.py` es el visitor principal y hereda un mixin por archivo. Cada mixin implementa solo los `visitX` de sus reglas.
- `codegen/emitter.py` hace lo mismo con los mixins de generación.
- Si un mixin necesita algo de otro, llama su método público. Nunca copia la lógica.
- `moves.py` y `borrows.py` se consultan entre sí con `moves.state(symbol)` y `borrows.is_borrowed(symbol)`. Ninguno modifica el estado del otro.

```python
class Analyzer(ItemsMixin, ControlMixin, MatchMixin, MovesMixin,     # A
               ScopesMixin, ExprsMixin, ArraysMixin, RefsMixin,      # B
               BorrowsMixin, RustiQVisitor):
    pass
```

### Formato de pruebas

- `tests/valid/structs_basico.rq` con `tests/valid/structs_basico.out`, la salida esperada exacta.
- `tests/invalid/move_dos_veces.rq` con la primera línea `// ERROR semantico E_USE_AFTER_MOVE 12:5`.

El runner compara fase, código, línea y columna. El mensaje puede cambiar sin romper pruebas.

## Etapas

Cada etapa termina con un entregable que se puede demostrar. Si una etapa se atrasa, se recorta alcance de esa etapa, no se mueve la fecha final.

### Etapa 0 · Base común · mar 3 a mié 4 nov

Juntos. Nadie empieza su carril hasta cerrar esto.

- [x] Crear repo, ramas protegidas y CI con un pytest vacío
- [x] Instalar ANTLR 4.13.2, wabt y wasmtime en ambas máquinas
- [x] Escribir los contratos 1 a 7 y el formato de pruebas
- [x] Esqueleto del `.g4` con todas las reglas y su dueño
- [x] Esqueleto de `analyzer.py` y `emitter.py` con los mixins vacíos
- [x] Escribir 10 programas de prueba válidos que cubran todo el lenguaje, sin salida esperada todavía
- [x] Escribir a mano un `hola.wat` que llame `print_i32`, convertirlo y ejecutarlo en wasmtime y en el navegador
- [x] Crear `docs/decisiones.md` con las decisiones asumidas

- [x] **Listo cuando:** CI pasa y `hola.wat` imprime en ambos runtimes.

### Etapa 1 · Parser y entorno de ejecución · jue 5 a dom 8 nov

**A**

- [x] Reglas del `.g4`: `functionDecl`, `structDecl`, `enumDecl`, `constDecl`, `type` y `pattern`
- [x] `runtime.wat`: bump allocator, `alloc`, `memcpy`, creación de String
- [x] `pipeline.py`: WAT a .wasm con wat2wasm, validación con wasm-validate, errores de backend como `CompileError`
- [x] Runner de pruebas que lee `.out` y la cabecera `// ERROR`
- [x] FastAPI con `/compile` que por ahora solo parsea y devuelve errores

**B**

- [ ] Lexer: identificadores, literales con escapes, comentarios `//` y `/* */`
- [ ] Reglas del `.g4`: `block`, `statement`, todos los niveles de `expression` y `place`
- [ ] Struct literal prohibido en condiciones de `if`, `while` y scrutinee de `match`
- [ ] Error listener propio que convierte errores de ANTLR a `CompileError`
- [ ] Host Python y `host.js` con los `print_*`
- [ ] Editor: CodeMirror, botones Compilar y Ejecutar, panel de errores, panel de salida, aviso de error de conexión
- [ ] Script `gen_grammar.sh`

- [ ] **Sincronización vie 6:** el `.g4` unido parsea los 10 programas. A partir de aquí la gramática cambia solo por PR acordado.

- [ ] **Sincronización dom 8:** el editor muestra errores sintácticos reales desde el servidor, con línea y columna subrayada.

### Etapa 2 · Tipos y generación básica · lun 9 a dom 15 nov

**A**

- [ ] Lunes 9: emisor base con módulo, funciones, locales y exports. Lo usan ambos
- [ ] Funciones y llamadas: firmas, número y tipo de argumentos, tipo de retorno, retorno faltante. Tipos y codegen
- [ ] Control de flujo: `if`, `while`, `loop`, `break`, `continue`, `return` y bloques con valor final. Tipos y codegen
- [ ] Constantes globales y locales
- [ ] Structs y tuplas: declaración, literal y acceso a campo. Tipos, layout y codegen
- [ ] Inválidos de sus características

**B**

- [ ] Lunes 9: tabla de símbolos con ámbitos y `uid` por símbolo. La usan ambos
- [ ] Ámbitos: uso sin declarar y declaración duplicada
- [ ] Literales y operadores: aritmética, comparaciones, `-` y `!`, `&&` y `||` con cortocircuito. Tipos y codegen. Aritmética i32 lista el martes 10
- [ ] Inferencia de `let` sin tipo, y `let` sin inicializador con uso antes de asignar
- [ ] Mutabilidad: `=`, `+=`, `-=`, `*=`, `/=` solo sobre valores `mut`
- [ ] Arrays: tipo, literal, indexación y chequeo de límites con `unreachable`. Tipos y codegen
- [ ] Inválidos de sus características

- [ ] **Sincronización mar 10:** un programa con función, `let`, aritmética e `if` compila de punta a punta.

- [ ] **Sincronización dom 15:** un programa con funciones, loops, structs y arrays compila, valida y se ejecuta desde el editor.

### Etapa 3 · Ownership y tipos compuestos · lun 16 a jue 19 nov

**A**

- [ ] Enums: declaración, `Enum::Variante`, tag y payload. Tipos y codegen
- [ ] Match: tipos de patrones, mismo tipo en todos los brazos, exhaustividad. Codegen sobre enums, literales, `_`, identificadores y tuplas
- [ ] Movimientos: estados disponible, movida y sin inicializar. Move al asignar, pasar y retornar usando `is_copy`
- [ ] Uso después de movimiento, reinicialización válida, y movimientos dentro de `if` y loops
- [ ] No mover un valor con préstamo activo, consultando `borrows`
- [ ] Copia de arrays y tuplas Copy con `memcpy`
- [ ] Inválidos de sus características

**B**

- [ ] Strings: literales en el segmento de datos, `print_str` y las operaciones que se decidan en P9
- [ ] Referencias: `&`, `&mut`, `*` de lectura y celdas para escalares con `address_taken`. Tipos y codegen
- [ ] Préstamos: varios `&` o un solo `&mut` hasta el fin del ámbito del préstamo
- [ ] `&mut` solo sobre variables `mut`, no asignar con préstamo activo, no retornar referencias a locales
- [ ] Resaltado de sintaxis RustiQ en el editor
- [ ] Inválidos de sus características

- [ ] **Sincronización mié 18:** `moves` y `borrows` integrados. Los inválidos de movimientos y préstamos pasan juntos.

- [ ] **Sincronización jue 19:** el ejemplo completo de la gramática compila y se ejecuta.

### Etapa 4 · Integración y entrega · vie 20 a dom 22 nov

Juntos.

- [ ] Viernes 20: congelamiento. Solo se corrigen bugs, nada nuevo
- [ ] Todas las pruebas pasan en CI
- [ ] Carpeta de evidencias: para cada programa válido, su .wat, su .wasm, la salida de wasm-validate y la salida de ejecución
- [ ] README con instalación y comandos en máquina limpia, probado por el que no lo escribió
- [ ] `docs/decisiones.md` completo: soportado, parcial, no soportado y diferencias con Rust
- [ ] Sábado 21: cada uno explica el módulo del otro en voz alta
- [ ] Domingo 22 antes de las 10:00 pm: entrega

### Después de la entrega

- [ ] Speech de 10 minutos siguiendo los 6 puntos del enunciado
- [ ] Guion de demo: un programa válido, uno con error de tipos, uno con uso después de movimiento, uno con préstamo incompatible
- [ ] Banco de preguntas técnicas: cada uno prepara 10 sobre el carril del otro

## Calendario y dependencias

&#91;embedded content: calendario por persona · 5 etapas, 6 sincronizaciones\]

A y B corren en paralelo. Cada sincronización es una prueba concreta que ambos verifican juntos antes de seguir. Si una falla, se aplica la tabla de riesgos.

## Pruebas y criterios de terminado

Meta al congelamiento: 30 programas válidos y 40 inválidos, todos en CI.

| Grupo                                   | Válidos | Inválidos | Dueño |
|-----------------------------------------|---------|-----------|-------|
| Léxico y sintaxis                       | 3       | 8         | B     |
| Ámbitos y declaraciones                 | 3       | 4         | B     |
| Funciones y control de flujo            | 6       | 6         | A     |
| Operadores, inferencia, mutabilidad     | 4       | 5         | B     |
| Structs, tuplas, enums, match           | 8       | 6         | A     |
| Movimientos                             | 2       | 6         | A     |
| Arrays, Strings, referencias, préstamos | 4       | 5         | B     |

Una tarea está terminada cuando:

- tiene al menos un programa de prueba que la cubre
- CI pasa en `main` después del merge
- el otro integrante revisó el PR
- si es del backend, el .wasm pasa `wasm-validate` y la salida coincide con el `.out`
- si cambia una decisión del lenguaje, `docs/decisiones.md` está actualizado

## Riesgos y recortes de alcance

Si algo se atrasa más de un día, se aplica el recorte en vez de empujar la fecha.

| Riesgo                                 | Señal                                            | Recorte                                                                                                                   |
|----------------------------------------|--------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| La gramática se atrasa                 | El vie 6 el .g4 unido no parsea los 10 programas | Cada uno arranca la etapa 2 con lo que ya parsea: funciones, i32, if, while. La gramática restante se termina en paralelo |
| El profesor cambia la gramática        | Respuesta a los puntos pendientes                | Cada extensión es una regla nueva en el .g4. Se regenera y se agrega un caso al typecheck y al codegen                    |
| Ownership en ramas y loops es complejo | El mié 18 fallan los inválidos de ramas          | Tratar todo movimiento condicional como movimiento definitivo. Es más estricto que Rust, se documenta                     |
| Lifetime de préstamos                  | Casos difíciles con préstamos que cruzan bloques | Préstamo activo hasta el final del ámbito léxico donde se creó. Sin análisis de último uso                                |
| Match con patrones anidados            | El codegen se complica                           | Soportar un solo nivel de anidación y documentarlo como limitación                                                        |
| Memoria del bump allocator             | Programas con loops que crean String             | `memory.grow` y documentar que no se libera memoria                                                                       |
| wabt no instala en alguna máquina      | Error en etapa 0                                 | Usar `wasmtime.wat2wasm` como conversor                                                                                   |
| Uno de los dos se enferma o se atrasa  | Una sincronización no se cumple                  | El otro toma las tareas pendientes. Posible por la revisión cruzada de PR                                                 |

Orden de recorte si falta tiempo al final: resaltado de sintaxis, chequeo de límites de arrays, patrones anidados, copia de arrays Copy. Nunca se recorta validación ni ejecución real del .wasm.
