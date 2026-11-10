grammar RustiQ;

// Version estricta: sigue el EBNF del documento.
// Unicas adiciones: EOF, la regla condition y el predicado de struct literal.
// Generar con:
//    antlr4 -Dlanguage=Python3 -visitor -no-listener RustiQ.g4

// Dueños de las reglas (ver plan de implementación):
//    A = Yerald: items, tipos, patrones, match, structs, enums y tuplas
//    B = Byron:  léxico, sentencias, expresiones, place, arrays
// Cada quien edita solo sus reglas. Si una regla ajena necesita cambio, se avisa.

@parser::members {
# Pila para desambiguar "identificador {" entre struct literal y bloque.
# En la condicion de if/while y en el valor de match no se admiten struct literals.
def ns(self):
    if not hasattr(self, "_ns"):
        self._ns = [False]
    return self._ns
}

// ---------------------------------------------------------------
// Programa e items
// ---------------------------------------------------------------

// Dueño: A (Yerald)
program
    : item* EOF
    ;

// Dueño: A (Yerald)
item
    : functionDecl
    | structDecl
    | enumDecl
    | constDecl
    ;

// Dueño: A (Yerald)
functionDecl
    : FN IDENT LPAREN parameterList? RPAREN (ARROW type)? block
    ;

// Dueño: A (Yerald)
parameterList
    : parameter (COMMA parameter)* COMMA?
    ;

// Dueño: A (Yerald)
parameter
    : MUT? IDENT COLON type
    ;

// Dueño: A (Yerald)
constDecl
    : CONST IDENT COLON type ASSIGN expression SEMI
    ;

// Dueño: A (Yerald)
structDecl
    : STRUCT IDENT LBRACE (fieldDecl (COMMA fieldDecl)* COMMA?)? RBRACE
    ;

// Dueño: A (Yerald)
fieldDecl
    : IDENT COLON type
    ;

// Dueño: A (Yerald)
enumDecl
    : ENUM IDENT LBRACE variantDecl (COMMA variantDecl)* COMMA? RBRACE
    ;

// Dueño: A (Yerald)
variantDecl
    : IDENT (LPAREN typeList RPAREN)?
    ;

// Dueño: A (Yerald)
typeList
    : type (COMMA type)* COMMA?
    ;

// ---------------------------------------------------------------
// Tipos
// ---------------------------------------------------------------

// Dueño: A (Yerald)
type
    : primitiveType                                        # PrimitiveT
    | STRING_TYPE                                          # StringT
    | LBRACK type SEMI INT_LIT RBRACK                      # ArrayT
    | LPAREN type (COMMA type)+ COMMA? RPAREN              # TupleT
    | AMP MUT? type                                        # RefT
    | IDENT                                                # NamedT
    ;

// Dueño: A (Yerald)
primitiveType
    : I32 | F64 | BOOL | CHAR
    ;

// ---------------------------------------------------------------
// Bloques y sentencias
// ---------------------------------------------------------------

// Dueño: B (Byron)
block
    : LBRACE statement* expression? RBRACE
    ;

// Dueño: B (Byron)
statement
    : letDecl                    # LetStmt
    | constLocalDecl             # ConstStmt
    | assignment SEMI            # AssignStmt
    | expression SEMI            # ExprStmt
    | returnStmt                 # ReturnS
    | breakStmt                  # BreakS
    | continueStmt               # ContinueS
    | whileStmt                  # WhileS
    | loopStmt                   # LoopS
    | ifStmt                     # IfS
    | block                      # BlockS
    ;

// Dueño: B (Byron)
letDecl
    : LET MUT? IDENT (COLON type)? (ASSIGN expression)? SEMI
    ;

// Dueño: B (Byron)
constLocalDecl
    : CONST IDENT COLON type ASSIGN expression SEMI
    ;

// Dueño: B (Byron)
assignment
    : place assignOp expression
    ;

// Dueño: B (Byron)
assignOp
    : ASSIGN | PLUSEQ | MINUSEQ | STAREQ | SLASHEQ
    ;

// Dueño: B (Byron)
returnStmt
    : RETURN expression? SEMI
    ;

// Dueño: B (Byron)
breakStmt
    : BREAK SEMI
    ;

// Dueño: B (Byron)
continueStmt
    : CONTINUE SEMI
    ;

// Dueño: B (Byron)
whileStmt
    : WHILE condition block
    ;

// Dueño: B (Byron)
loopStmt
    : LOOP block
    ;

// Dueño: B (Byron)
ifStmt
    : IF condition block (ELSE (block | ifStmt))?
    ;

// Expresion sin struct literals (para if, while y match).
// Dueño: B (Byron)
condition
    : {self.ns().append(True)} expression {self.ns().pop()}
    ;

// ---------------------------------------------------------------
// Expresiones (precedencia de menor a mayor)
// ---------------------------------------------------------------

// Dueño: B (Byron)
expression
    : logicalOr
    ;

// Dueño: B (Byron)
logicalOr
    : logicalAnd (OR logicalAnd)*
    ;

// Dueño: B (Byron)
logicalAnd
    : comparison (AND comparison)*
    ;

// Dueño: B (Byron)
comparison
    : additive (relOp additive)?
    ;

// Dueño: B (Byron)
relOp
    : EQEQ | NEQ | LT | LE | GT | GE
    ;

// Dueño: B (Byron)
additive
    : multiplicative ((PLUS | MINUS) multiplicative)*
    ;

// Dueño: B (Byron)
multiplicative
    : unary ((STAR | SLASH | PERCENT) unary)*
    ;

// Dueño: B (Byron)
unary
    : (MINUS | BANG | AMP MUT? | STAR)? postfix
    ;

// Dueño: B (Byron)
postfix
    : primary (callSuffix | fieldSuffix | indexSuffix)*
    ;

// Dueño: B (Byron)
callSuffix
    : LPAREN argumentList? RPAREN
    ;

// Dueño: B (Byron)
argumentList
    : expression (COMMA expression)* COMMA?
    ;

// Dueño: B (Byron)
fieldSuffix
    : DOT IDENT
    ;

// Dueño: B (Byron)
indexSuffix
    : LBRACK expression RBRACK
    ;

// Dueño: B (Byron)
primary
    : literal                                                            # LiteralP
    | {not self.ns()[-1]}? structLiteral                                 # StructP
    | enumValue                                                          # EnumP
    | IDENT                                                              # IdentP
    | tupleLiteral                                                       # TupleP
    | arrayLiteral                                                       # ArrayP
    | matchExpr                                                          # MatchP
    | LPAREN {self.ns().append(False)} expression {self.ns().pop()} RPAREN   # ParenP
    | block                                                              # BlockP
    ;

// Dueño: A (Yerald)
tupleLiteral
    : LPAREN expression (COMMA expression)+ COMMA? RPAREN
    ;

// Dueño: B (Byron)
arrayLiteral
    : LBRACK expression (COMMA expression)* COMMA? RBRACK
    ;

// Dueño: A (Yerald)
structLiteral
    : IDENT LBRACE (fieldInit (COMMA fieldInit)* COMMA?)? RBRACE
    ;

// Dueño: A (Yerald)
fieldInit
    : IDENT COLON expression
    ;

// Dueño: A (Yerald)
enumValue
    : IDENT COLONCOLON IDENT (LPAREN argumentList RPAREN)?
    ;

// ---------------------------------------------------------------
// Match y patrones
// ---------------------------------------------------------------

// Dueño: A (Yerald)
matchExpr
    : MATCH condition LBRACE matchArm (COMMA matchArm)* COMMA? RBRACE
    ;

// Dueño: A (Yerald)
matchArm
    : pattern FATARROW expression
    ;

// Dueño: A (Yerald)
pattern
    : UNDERSCORE                                               # WildcardPat
    | literal                                                  # LiteralPat
    | IDENT COLONCOLON IDENT (LPAREN patternList RPAREN)?     # EnumPat
    | IDENT                                                    # BindingPat
    | LPAREN pattern (COMMA pattern)+ COMMA? RPAREN           # TuplePat
    ;

// Dueño: A (Yerald)
patternList
    : pattern (COMMA pattern)* COMMA?
    ;

// Dueño: B (Byron)
place
    : IDENT (DOT IDENT | LBRACK expression RBRACK)*
    ;

// ---------------------------------------------------------------
// Literales
// ---------------------------------------------------------------

// Dueño: B (Byron)
literal
    : INT_LIT
    | FLOAT_LIT
    | TRUE
    | FALSE
    | CHAR_LIT
    | STRING_LIT
    ;

// ---------------------------------------------------------------
// Lexer
// Las palabras reservadas van antes de IDENT.
// ---------------------------------------------------------------

// Dueño de todo el léxico: B (Byron)
// Palabras reservadas
FN          : 'fn' ;
STRUCT      : 'struct' ;
ENUM        : 'enum' ;
CONST       : 'const' ;
LET         : 'let' ;
MUT         : 'mut' ;
RETURN      : 'return' ;
BREAK       : 'break' ;
CONTINUE    : 'continue' ;
WHILE       : 'while' ;
LOOP        : 'loop' ;
IF          : 'if' ;
ELSE        : 'else' ;
MATCH       : 'match' ;
TRUE        : 'true' ;
FALSE       : 'false' ;
I32         : 'i32' ;
F64         : 'f64' ;
BOOL        : 'bool' ;
CHAR        : 'char' ;
STRING_TYPE : 'String' ;

// Operadores de varios caracteres
ARROW       : '->' ;
FATARROW    : '=>' ;
COLONCOLON  : '::' ;
EQEQ        : '==' ;
NEQ         : '!=' ;
LE          : '<=' ;
GE          : '>=' ;
AND         : '&&' ;
OR          : '||' ;
PLUSEQ      : '+=' ;
MINUSEQ     : '-=' ;
STAREQ      : '*=' ;
SLASHEQ     : '/=' ;

// Operadores de un caracter
ASSIGN      : '=' ;
LT          : '<' ;
GT          : '>' ;
PLUS        : '+' ;
MINUS       : '-' ;
STAR        : '*' ;
SLASH       : '/' ;
PERCENT     : '%' ;
BANG        : '!' ;
AMP         : '&' ;

// Puntuacion
LPAREN      : '(' ;
RPAREN      : ')' ;
LBRACE      : '{' ;
RBRACE      : '}' ;
LBRACK      : '[' ;
RBRACK      : ']' ;
COMMA       : ',' ;
SEMI        : ';' ;
COLON       : ':' ;
DOT         : '.' ;

UNDERSCORE  : '_' ;

IDENT
    : [a-zA-Z_] [a-zA-Z0-9_]*
    ;

FLOAT_LIT : DIGIT+ '.' DIGIT+ ;
INT_LIT   : DIGIT+ ;

CHAR_LIT
    : '\'' ( ~['\\\r\n] | ESC ) '\''
    ;

STRING_LIT
    : '"' ( ~["\\\r\n] | ESC )* '"'
    ;

fragment ESC   : '\\' [\\ntr"'] ;
fragment DIGIT : [0-9] ;

LINE_COMMENT  : '//' ~[\r\n]* -> skip ;
BLOCK_COMMENT : '/*' .*? '*/' -> skip ;
WS            : [ \t\r\n]+ -> skip ;