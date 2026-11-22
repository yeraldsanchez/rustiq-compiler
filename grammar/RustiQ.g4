grammar RustiQ;

// Version estricta: sigue el EBNF del documento.
// Unicas adiciones: EOF, la regla condition y el predicado de struct literal.
// Generar con:
//    antlr4 -Dlanguage=Python3 -visitor -no-listener RustiQ.g4

@parser::members {
# Pila para desambiguar "identificador {" entre struct literal y bloque.
# En la condicion de if/while y en el valor de match no se admiten struct literals,
# salvo dentro de (), [], {} o los argumentos de una llamada, donde ya no hay ambigüedad.
def ns(self):
    if not hasattr(self, "_ns"):
        self._ns = [False]
    return self._ns
}

// ---------------------------------------------------------------
// Programa e items
// ---------------------------------------------------------------

program
    : item* EOF
    ;

item
    : functionDecl
    | structDecl
    | enumDecl
    | constDecl
    ;

functionDecl
    : FN IDENT LPAREN parameterList? RPAREN (ARROW type)? block
    ;

parameterList
    : parameter (COMMA parameter)* COMMA?
    ;

parameter
    : MUT? IDENT COLON type
    ;

constDecl
    : CONST IDENT COLON type ASSIGN expression SEMI
    ;

structDecl
    : STRUCT IDENT LBRACE (fieldDecl (COMMA fieldDecl)* COMMA?)? RBRACE
    ;

fieldDecl
    : IDENT COLON type
    ;

enumDecl
    : ENUM IDENT LBRACE variantDecl (COMMA variantDecl)* COMMA? RBRACE
    ;

variantDecl
    : IDENT (LPAREN typeList RPAREN)?
    ;

typeList
    : type (COMMA type)* COMMA?
    ;

// ---------------------------------------------------------------
// Tipos
// ---------------------------------------------------------------

type
    : primitiveType                                       # PrimitiveT
    | STRING_TYPE                                         # StringT
    | LBRACK type SEMI INT_LIT RBRACK                     # ArrayT
    | LPAREN type (COMMA type)+ COMMA? RPAREN             # TupleT
    | AMP MUT? type                                       # RefT
    // El lexer lee "&&" como AND; aquí equivale a & (& [mut] type). Ver P10.
    | AND MUT? type                                       # RefRefT
    | IDENT                                               # NamedT
    ;

primitiveType
    : I32 | F64 | BOOL | CHAR
    ;

// ---------------------------------------------------------------
// Bloques y sentencias
// ---------------------------------------------------------------

block
    : LBRACE {self.ns().append(False)} statement* expression? {self.ns().pop()} RBRACE
    ;

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

letDecl
    : LET MUT? IDENT (COLON type)? (ASSIGN expression)? SEMI
    ;

constLocalDecl
    : CONST IDENT COLON type ASSIGN expression SEMI
    ;

assignment
    : place assignOp expression
    ;

assignOp
    : ASSIGN | PLUSEQ | MINUSEQ | STAREQ | SLASHEQ
    ;

returnStmt
    : RETURN expression? SEMI
    ;

breakStmt
    : BREAK SEMI
    ;

continueStmt
    : CONTINUE SEMI
    ;

whileStmt
    : WHILE condition block
    ;

loopStmt
    : LOOP block
    ;

ifStmt
    : IF condition block (ELSE (block | ifStmt))?
    ;

// Expresion sin struct literals (para if, while y match).
condition
    : {self.ns().append(True)} expression {self.ns().pop()}
    ;

// ---------------------------------------------------------------
// Expresiones (precedencia de menor a mayor)
// ---------------------------------------------------------------

expression
    : logicalOr
    ;

logicalOr
    : logicalAnd (OR logicalAnd)*
    ;

logicalAnd
    : comparison (AND comparison)*
    ;

comparison
    : additive (relOp additive)?
    ;

relOp
    : EQEQ | NEQ | LT | LE | GT | GE
    ;

additive
    : multiplicative ((PLUS | MINUS) multiplicative)*
    ;

multiplicative
    : unary ((STAR | SLASH | PERCENT) unary)*
    ;

unary
    : (MINUS | BANG | AMP MUT? | STAR)? postfix
    ;

postfix
    : primary (callSuffix | fieldSuffix | indexSuffix)*
    ;

callSuffix
    : LPAREN {self.ns().append(False)} argumentList? {self.ns().pop()} RPAREN
    ;

argumentList
    : expression (COMMA expression)* COMMA?
    ;

fieldSuffix
    : DOT IDENT
    ;

indexSuffix
    : LBRACK {self.ns().append(False)} expression {self.ns().pop()} RBRACK
    ;

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

tupleLiteral
    : LPAREN {self.ns().append(False)} expression (COMMA expression)+ COMMA? {self.ns().pop()} RPAREN
    ;

arrayLiteral
    : LBRACK {self.ns().append(False)} expression (COMMA expression)* COMMA? {self.ns().pop()} RBRACK
    ;

structLiteral
    : IDENT LBRACE (fieldInit (COMMA fieldInit)* COMMA?)? RBRACE
    ;

fieldInit
    : IDENT COLON expression
    ;

enumValue
    : IDENT COLONCOLON IDENT (LPAREN {self.ns().append(False)} argumentList {self.ns().pop()} RPAREN)?
    ;

// ---------------------------------------------------------------
// Match y patrones
// ---------------------------------------------------------------

matchExpr
    : MATCH condition LBRACE matchArm (COMMA matchArm)* COMMA? RBRACE
    ;

matchArm
    : pattern FATARROW expression
    ;

pattern
    : UNDERSCORE                                               # WildcardPat
    | literal                                                  # LiteralPat
    | IDENT COLONCOLON IDENT (LPAREN patternList RPAREN)?     # EnumPat
    | IDENT                                                    # BindingPat
    | LPAREN pattern (COMMA pattern)+ COMMA? RPAREN           # TuplePat
    ;

patternList
    : pattern (COMMA pattern)* COMMA?
    ;

place
    : IDENT (DOT IDENT | LBRACK expression RBRACK)*
    ;

// ---------------------------------------------------------------
// Literales
// ---------------------------------------------------------------

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

// Tokens de error, en el canal oculto: el parser no los ve y el pipeline los convierte en errores
// léxicos con código propio. Van después de los literales válidos: con el mismo
// largo gana el primero, así solo coinciden cuando el literal está mal.
BAD_STRING          : '"' ( ~["\\\r\n] | '\\' ~[\r\n] )* '"' -> channel(HIDDEN) ;   // escape no válido
UNTERMINATED_STRING : '"' ( ~["\\\r\n] | '\\' ~[\r\n] )* -> channel(HIDDEN) ;       // sin '"' antes del fin de línea
BAD_CHAR            : '\'' ( ~['\\\r\n] | '\\' ~[\r\n] )* '\'' -> channel(HIDDEN) ;  // vacío, varios caracteres o escape no válido
UNTERMINATED_CHAR   : '\'' ( ~['\\\r\n] | '\\' ~[\r\n] )* -> channel(HIDDEN) ;
UNTERMINATED_COMMENT: '/*' ( ~'*' | '*'+ ~[*/] )* '*'* EOF -> channel(HIDDEN) ;

fragment ESC   : '\\' [\\ntr"'] ;
fragment DIGIT : [0-9] ;

LINE_COMMENT  : '//' ~[\r\n]* -> skip ;
BLOCK_COMMENT : '/*' .*? '*/' -> skip ;
WS            : [ \t\r\n]+ -> skip ;