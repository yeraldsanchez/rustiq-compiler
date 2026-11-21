"""Pruebas unitarias y de ejecución Wasm para Strings, Referencias y Préstamos (Carril B - Etapa 3)."""

from antlr4 import CommonTokenStream, InputStream
from wasmtime import Engine, FuncType, Linker, Module, Store, ValType

from rustiq.codegen.emitter import Emitter
from rustiq.errors import (
    E_ASSIGN_WHILE_BORROWED,
    E_BAD_OPERAND,
    E_BORROW_CONFLICT,
    E_BORROW_MUT_IMMUTABLE,
    E_RETURN_LOCAL_REF,
)
from rustiq.generated.RustiQLexer import RustiQLexer
from rustiq.generated.RustiQParser import RustiQParser
from rustiq.pipeline import assemble
from rustiq.semantic.analyzer import Analyzer


def _analyze(source: str):
    lexer = RustiQLexer(InputStream(source))
    parser = RustiQParser(CommonTokenStream(lexer))
    tree = parser.program()
    assert parser.getNumberOfSyntaxErrors() == 0
    info, errors = Analyzer().analyze(tree)
    return tree, info, errors


def _run_wasm(source: str) -> list[str]:
    tree, info, errors = _analyze(source)
    assert errors == [], errors
    wat = Emitter(info).generate(tree)
    wasm_bytes = assemble(wat)

    out: list[str] = []
    engine = Engine()
    store = Store(engine)
    linker = Linker(engine)

    linker.define_func("env", "print_i32", FuncType([ValType.i32()], []), lambda v: out.append(str(v)))
    linker.define_func("env", "print_f64", FuncType([ValType.f64()], []), lambda v: out.append(str(v)))
    linker.define_func(
        "env",
        "print_bool",
        FuncType([ValType.i32()], []),
        lambda v: out.append("true" if v else "false"),
    )
    linker.define_func("env", "print_char", FuncType([ValType.i32()], []), lambda v: out.append(chr(v)))

    # Referencia a la memoria exportada del módulo para leer Strings en print_str
    mem_holder: list = []

    def _print_str(ptr: int):
        mem = mem_holder[0]
        raw = mem.read(store)
        length = int.from_bytes(raw[ptr : ptr + 4], "little")
        text = bytes(raw[ptr + 4 : ptr + 4 + length]).decode("utf-8")
        out.append(text)

    linker.define_func("env", "print_str", FuncType([ValType.i32()], []), _print_str)

    instance = linker.instantiate(store, Module(engine, wasm_bytes))
    mem_holder.append(instance.exports(store)["memory"])
    instance.exports(store)["main"](store)
    return out


# ---------------------------------------------------------------
# 1. Strings: literales en segmento (data ...), UTF-8 y print_str
# ---------------------------------------------------------------

def test_string_literal_y_print_str():
    src = """
    fn saludar(msg: String) {
        print_str(msg);
    }

    fn main() {
        let s: String = "Hola RustiQ\\n";
        let utf8 = "Año 2026";
        saludar(s);
        print_str(utf8);
    }
    """
    salida = _run_wasm(src)
    assert salida == ["Hola RustiQ\n", "Año 2026"]


# ---------------------------------------------------------------
# 2. Referencias (&, &mut, *) y celdas heap con address_taken
# ---------------------------------------------------------------

def test_referencia_escalar_con_address_taken_y_deref():
    src = """
    fn leer_doble(r: &i32) -> i32 {
        return *r + *r;
    }

    fn main() {
        let mut x: i32 = 21;
        let r: &i32 = &x;
        let res: i32 = leer_doble(r);
        print_i32(res);
    }
    """
    _, info, errors = _analyze(src)
    assert errors == []

    # Verificar que `x` quedó marcado con address_taken = True
    simbolos_x = [s for s in info.symbol._values.values() if s.name == "x" and s.kind == "local"]
    assert any(s.address_taken for s in simbolos_x)

    salida = _run_wasm(src)
    assert salida == ["42"]


def test_referencia_mut_a_struct_y_prestamo_temporal_en_llamada():
    src = """
    struct Contador {
        valor: i32,
    }

    fn incrementar(c: &mut Contador) {
        c.valor = c.valor + 1;
    }

    fn main() {
        let mut c: Contador = Contador { valor: 10 };
        incrementar(&mut c);
        // El préstamo temporal de la llamada ya expiró al terminar la sentencia
        incrementar(&mut c);
        print_i32(c.valor);
    }
    """
    salida = _run_wasm(src)
    assert salida == ["12"]


# ---------------------------------------------------------------
# 3. Préstamos válidos: múltiples & y liberación al fin de bloque (G9)
# ---------------------------------------------------------------

def test_multiples_prestamos_inmutables_y_liberacion_por_bloque():
    src = """
    fn main() {
        let mut x: i32 = 5;
        {
            let r1: &i32 = &x;
            let r2: &i32 = &x;
            print_i32(*r1 + *r2);
        }
        // Al salir del bloque, r1 y r2 mueren y ya se puede mutar o tomar &mut
        x = 15;
        let r_mut: &mut i32 = &mut x;
        print_i32(*r_mut);
    }
    """
    salida = _run_wasm(src)
    assert salida == ["10", "15"]


# ---------------------------------------------------------------
# 4. Casos inválidos de referencias y préstamos
# ---------------------------------------------------------------

def test_error_borrow_mut_sobre_variable_inmutable():
    src = """
    fn main() {
        let x: i32 = 10;
        let r = &mut x;
    }
    """
    _, _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].code == E_BORROW_MUT_IMMUTABLE


def test_error_conflicto_borrow_mut_con_inmutable_activo():
    src = """
    fn main() {
        let mut x: i32 = 10;
        let r1 = &x;
        let r2 = &mut x;
    }
    """
    _, _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].code == E_BORROW_CONFLICT


def test_error_conflicto_borrow_inmutable_con_mut_activo():
    src = """
    fn main() {
        let mut x: i32 = 10;
        let r1 = &mut x;
        let r2 = &x;
    }
    """
    _, _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].code == E_BORROW_CONFLICT


def test_error_asignar_mientras_esta_prestado():
    src = """
    fn main() {
        let mut x: i32 = 10;
        let r = &x;
        x = 20;
    }
    """
    _, _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].code == E_ASSIGN_WHILE_BORROWED


def test_error_retornar_referencia_local():
    src = """
    fn fuga() -> &i32 {
        let x: i32 = 99;
        return &x;
    }
    fn main() {}
    """
    _, _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].code == E_RETURN_LOCAL_REF


def test_error_desreferenciar_no_referencia():
    src = """
    fn main() {
        let x: i32 = 5;
        let y = *x;
    }
    """
    _, _, errors = _analyze(src)
    assert len(errors) == 1
    assert errors[0].code == E_BAD_OPERAND