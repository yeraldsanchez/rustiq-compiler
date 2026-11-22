"""Contrato 1: formato único de errores.

Todas las fases reportan igual. El editor, el servidor y las pruebas dependen
de este formato. Un cambio aquí va en su propio PR.
"""

from dataclasses import asdict, dataclass

# Fases
LEXICO = "lexico"
SINTACTICO = "sintactico"
SEMANTICO = "semantico"
BACKEND = "backend"

PHASES = (LEXICO, SINTACTICO, SEMANTICO, BACKEND)

# Códigos de error. Agregar uno nuevo no rompe nada.
# Léxico
E_INVALID_CHAR = "E_INVALID_CHAR"
E_UNTERMINATED_STRING = "E_UNTERMINATED_STRING"
E_UNTERMINATED_COMMENT = "E_UNTERMINATED_COMMENT"
E_INVALID_ESCAPE = "E_INVALID_ESCAPE"

# Sintáctico
E_SYNTAX = "E_SYNTAX"

# Semántico: ámbitos y declaraciones
E_UNDECLARED = "E_UNDECLARED"
E_REDECLARED = "E_REDECLARED"

# Semántico: tipos
E_TYPE_MISMATCH = "E_TYPE_MISMATCH"
E_UNKNOWN_TYPE = "E_UNKNOWN_TYPE"
E_CANNOT_INFER = "E_CANNOT_INFER"
E_BAD_OPERAND = "E_BAD_OPERAND"
E_INT_OUT_OF_RANGE = "E_INT_OUT_OF_RANGE"
E_ARG_COUNT = "E_ARG_COUNT"
E_NOT_CALLABLE = "E_NOT_CALLABLE"
E_UNKNOWN_FIELD = "E_UNKNOWN_FIELD"
E_MISSING_FIELD = "E_MISSING_FIELD"
E_UNKNOWN_VARIANT = "E_UNKNOWN_VARIANT"
E_NOT_EXHAUSTIVE = "E_NOT_EXHAUSTIVE"
E_BAD_PATTERN = "E_BAD_PATTERN"
E_BAD_INDEX = "E_BAD_INDEX"
E_BAD_RETURN = "E_BAD_RETURN"
E_BREAK_OUTSIDE_LOOP = "E_BREAK_OUTSIDE_LOOP"
E_BAD_MAIN = "E_BAD_MAIN"

# Semántico: mutabilidad, ownership y préstamos
E_ASSIGN_IMMUTABLE = "E_ASSIGN_IMMUTABLE"
E_UNINITIALIZED = "E_UNINITIALIZED"
E_USE_AFTER_MOVE = "E_USE_AFTER_MOVE"
E_MOVE_WHILE_BORROWED = "E_MOVE_WHILE_BORROWED"
E_MOVE_OUT_OF_PLACE = "E_MOVE_OUT_OF_PLACE"
E_BORROW_CONFLICT = "E_BORROW_CONFLICT"
E_BORROW_MUT_IMMUTABLE = "E_BORROW_MUT_IMMUTABLE"
E_ASSIGN_WHILE_BORROWED = "E_ASSIGN_WHILE_BORROWED"
E_RETURN_LOCAL_REF = "E_RETURN_LOCAL_REF"

# Backend
E_WAT_INVALID = "E_WAT_INVALID"
E_WASM_INVALID = "E_WASM_INVALID"
E_INTERNAL = "E_INTERNAL"


@dataclass
class CompileError:
    phase: str  # una de PHASES
    code: str  # "E_UNDECLARED", "E_TYPE_MISMATCH", ...
    message: str  # en español
    line: int  # desde 1
    column: int  # desde 1. ANTLR da columnas desde 0, se suma 1
    length: int = 1  # para subrayar en el editor

    def to_dict(self) -> dict:
        """Forma JSON que devuelve el servidor."""
        return asdict(self)
