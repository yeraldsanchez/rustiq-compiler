# RustiQ: Gramática EBNF de un subconjunto de Rust

Nov 3, 2026

RustiQ · Lenguaje de programación inspirado en Rust

*Una especificación inicial para un lenguaje estático con tipos algebraicos y análisis simplificado de ownership y borrowing.*

## Características generales

RustiQ es un lenguaje inspirado en Rust, diseñado como un subconjunto implementable mediante un compilador propio. No pretende ser compatible con toda la sintaxis ni con toda la semántica del Rust oficial.

Un programa está formado por declaraciones de estructuras, enumeraciones, constantes y funciones. La función de entrada convencional es main; se permiten funciones auxiliares.

Tipos incluidos: i32, f64, bool, char y String; arrays de longitud fija y tuplas; structs con campos; enums con variantes unitarias o con datos.

Incluye variables let y let mut, funciones tipadas, expresiones, bloques, if/else, while, loop, break, continue, return y match.

Ownership y borrowing forman parte del análisis semántico: movimiento de valores no copiables, referencias inmutables &T, referencias mutables &mut T y comprobaciones simplificadas de mutabilidad, préstamos activos y uso después de movimiento.

El subconjunto inicial deja fuera genéricos, traits, lifetimes explícitos, macros, closures, async/await y unsafe. Podrán incorporarse en versiones posteriores.

Se recomienda que el compilador use un AST propio, una fase de análisis semántico y una representación intermedia independiente del backend. WebAssembly puede ser uno de los destinos de generación.

## Convenciones de la notación EBNF

- Los terminales se escriben entre comillas dobles, por ejemplo "fn" o ";".
- El símbolo = define una producción y ; la termina.
- El operador | expresa alternativas.
- Los corchetes \[ ... \] indican una parte opcional (cero o una vez).
- Las llaves { ... } indican repetición de cero o más veces.
- Los paréntesis agrupan elementos.
- Los comentarios de esta especificación describen decisiones del subconjunto y no forman parte de la gramática.

## Gramática EBNF

```
program          = { item } ;

item              = functionDecl
                  | structDecl
                  | enumDecl
                  | constDecl ;

functionDecl      = "fn" identifier "(" [ parameterList ] ")"
                    [ "->" type ] block ;

parameterList     = parameter { "," parameter } [ "," ] ;
parameter         = [ "mut" ] identifier ":" type ;

constDecl         = "const" identifier ":" type "=" expression ";" ;

structDecl        = "struct" identifier "{"
                    [ fieldDecl { "," fieldDecl } [ "," ] ]
                    "}" ;
fieldDecl         = identifier ":" type ;

enumDecl          = "enum" identifier "{"
                    variantDecl { "," variantDecl } [ "," ]
                    "}" ;
variantDecl       = identifier [ "(" typeList ")" ] ;
typeList          = type { "," type } [ "," ] ;

type              = primitiveType
                  | "String"
                  | arrayType
                  | tupleType
                  | referenceType
                  | identifier ;

primitiveType     = "i32" | "f64" | "bool" | "char" ;
arrayType         = "[" type ";" integerLiteral "]" ;
tupleType         = "(" type "," type { "," type } [ "," ] ")" ;
referenceType     = "&" [ "mut" ] type ;

block             = "{" { statement } [ expression ] "}" ;

statement         = letDecl
                  | constLocalDecl
                  | assignment ";"
                  | expression ";"
                  | returnStmt
                  | breakStmt
                  | continueStmt
                  | whileStmt
                  | loopStmt
                  | ifStmt
                  | block ;

letDecl           = "let" [ "mut" ] identifier [ ":" type ]
                    [ "=" expression ] ";" ;
constLocalDecl    = "const" identifier ":" type "=" expression ";" ;
assignment        = place assignOp expression ;
assignOp          = "=" | "+=" | "-=" | "*=" | "/=" ;

returnStmt        = "return" [ expression ] ";" ;
breakStmt         = "break" ";" ;
continueStmt      = "continue" ";" ;
whileStmt         = "while" expression block ;
loopStmt          = "loop" block ;
ifStmt            = "if" expression block [ "else" ( block | ifStmt ) ] ;

expression        = logicalOr ;
logicalOr         = logicalAnd { "||" logicalAnd } ;
logicalAnd        = comparison { "&&" comparison } ;
comparison        = additive [ relOp additive ] ;
relOp             = "==" | "!=" | "<" | "<=" | ">" | ">=" ;
additive          = multiplicative { ("+" | "-") multiplicative } ;
multiplicative    = unary { ("*" | "/" | "%") unary } ;
unary             = [ "-" | "!" | "&" [ "mut" ] | "*" ] postfix ;
postfix           = primary { callSuffix | fieldSuffix | indexSuffix } ;
callSuffix        = "(" [ argumentList ] ")" ;
argumentList      = expression { "," expression } [ "," ] ;
fieldSuffix       = "." identifier ;
indexSuffix       = "[" expression "]" ;

primary           = literal
                  | identifier
                  | tupleLiteral
                  | arrayLiteral
                  | structLiteral
                  | enumValue
                  | matchExpr
                  | "(" expression ")"
                  | block ;

tupleLiteral      = "(" expression "," expression
                    { "," expression } [ "," ] ")" ;
arrayLiteral      = "[" expression { "," expression } [ "," ] "]" ;
structLiteral     = identifier "{" [ fieldInit { "," fieldInit } [ "," ] ] "}" ;
fieldInit         = identifier ":" expression ;
enumValue         = identifier "::" identifier [ "(" argumentList ")" ] ;

matchExpr         = "match" expression "{"
                    matchArm { "," matchArm } [ "," ] "}" ;
matchArm          = pattern "=>" expression ;
pattern           = "_"
                  | literal
                  | identifier
                  | identifier "::" identifier [ "(" patternList ")" ]
                  | "(" pattern "," pattern { "," pattern } [ "," ] ")" ;
patternList       = pattern { "," pattern } [ "," ] ;

place             = identifier { "." identifier | "[" expression "]" } ;

literal           = integerLiteral
                  | floatLiteral
                  | booleanLiteral
                  | charLiteral
                  | stringLiteral ;
booleanLiteral    = "true" | "false" ;

identifier        = letter { letter | digit | "_" } ;
integerLiteral    = digit { digit } ;
floatLiteral      = digit { digit } "." digit { digit } ;
charLiteral       = "'" charContent "'" ;
stringLiteral     = '"' { stringContent } '"' ;

letter            = "A"…"Z" | "a"…"z" ;
digit             = "0"…"9" ;
charContent       = any Unicode scalar except "'" and line break,
                    or an escape sequence ;
stringContent     = any Unicode scalar except '"' and line break,
                    or an escape sequence ;
```

## Reglas léxicas y notas de alcance

- Los identificadores comienzan con una letra ASCII o guion bajo y continúan con letras, dígitos o guion bajo. Esta decisión puede ampliarse para admitir identificadores Unicode.
- Los literales char representan un único valor escalar Unicode. Los literales de cadena admiten secuencias de escape como `\\`, `\n`, `\t`, `\r`, `\"` y `\'`.
- Se permiten comentarios de línea // ... y comentarios de bloque /\* ... \*/. En la versión inicial no se admiten comentarios de bloque anidados.
- La gramática reconoce la forma sintáctica de referencias y asignaciones; la validez de los préstamos, movimientos, mutabilidad, tipos y ámbitos se comprueba semánticamente.
- Los bloques se interpretan como una secuencia de sentencias y, opcionalmente, una expresión final sin punto y coma. La expresión final determina el valor del bloque.
- Los arrays tienen longitud fija indicada en el tipo. Las tuplas requieren al menos dos elementos en su tipo y en su literal.
- Para mantener la primera versión acotada, se recomienda que las cadenas tengan tipo propietario String; no se incorpora el tipo str ni lifetimes explícitos.
- La gramática EBNF es una especificación conceptual. Para implementarla en ANTLR4 será necesario adaptar las producciones, especialmente los prefijos de expresiones, los bloques y las ambigüedades entre structLiteral y bloques.

## Ejemplo de uso

El siguiente programa combina structs, enums, match, funciones, tipos básicos, arrays, tuplas y préstamos. Ilustra el estilo previsto para RustiQ; las reglas exactas de ownership y borrowing deben implementarse en el análisis semántico.

```
struct Punto {
    x: f64,
    y: f64,
}

enum Estado {
    Pendiente,
    Completado(i32),
    Error(String),
}

fn mover_x(p: &mut Punto, dx: f64) {
    p.x = p.x + dx;
}

fn describir(estado: Estado) -> i32 {
    match estado {
        Estado::Pendiente => 0,
        Estado::Completado(codigo) => codigo,
        Estado::Error(_) => -1,
    }
}

fn main() {
    let mut p = Punto { x: 1.0, y: 2.0 };
    mover_x(&mut p, 3.0);

    let estado = Estado::Completado(200);
    let codigo = describir(estado);

    let dimensiones: (f64, f64) = (p.x, p.y);
    let muestras: [i32; 3] = [10, 20, 30];
    let correcto: bool = codigo == 200;
    let inicial: char = 'R';

    if correcto {
        p.y = p.y + 1.0;
    }
}
```

### Qué demuestra el ejemplo

- Punto es un struct con campos f64 y acceso mediante punto.
- Estado es un enum con variantes sin datos, con un i32 o con un String.
- mover\_x recibe una referencia mutable y modifica el campo x sin tomar la propiedad del Punto.
- describir recibe Estado por valor; la llamada mueve la propiedad de estado a la función, por lo que el programa no vuelve a usar esa variable.
- match contempla todas las variantes de Estado y devuelve un i32 en todos los brazos.
- main muestra tuplas, arrays, bool y char. Las variables dimensiones, muestras e inicial son ejemplos de tipos admitidos aunque no se usen posteriormente.
- El compilador debe comprobar que p sea mutable cuando se pasa como &mut Punto y que no existan préstamos incompatibles activos.

## Orientación para la implementación

- Frontend sugerido: ANTLR4 para el análisis léxico y sintáctico, seguido de la construcción de un AST propio.
- Análisis semántico sugerido: resolución de nombres, comprobación de tipos, validación de match, estado de propiedad (disponible, movido o sin inicializar) y registro de préstamos por ámbito.
- Backend posible: una IR tipada independiente del destino y generación de WAT/Wasm. Los structs, enums, arrays, tuplas y String requieren un layout y convenciones de memoria definidos.
- El lenguaje se denomina RustiQ para comunicar que es un subconjunto inspirado en Rust, no una implementación oficial ni totalmente compatible con Rust.

*Especificación inicial del subconjunto · Gramática EBNF*
