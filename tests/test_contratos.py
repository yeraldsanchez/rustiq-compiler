from rustiq.errors import PHASES, SEMANTICO, E_UNDECLARED, CompileError
from rustiq.semantic.info import NodeProperty, SemanticInfo
from rustiq.types import (
    BOOL, CHAR, F64, I32, STRING, UNIT, ArrayT, EnumT, RefT, StructT, TupleT, is_copy,
)


def test_compile_error_to_dict():
    e = CompileError(SEMANTICO, E_UNDECLARED, "x no está declarada", 3, 5)
    assert SEMANTICO in PHASES
    assert e.to_dict() == {
        "phase": "semantico", "code": "E_UNDECLARED",
        "message": "x no está declarada", "line": 3, "column": 5, "length": 1,
    }


def test_is_copy_primitivos_y_unit():
    for t in (I32, F64, BOOL, CHAR, UNIT):
        assert is_copy(t)
    assert not is_copy(STRING)


def test_is_copy_referencias():
    assert is_copy(RefT(STRING, mutable=False))
    assert not is_copy(RefT(I32, mutable=True))


def test_is_copy_compuestos_siempre_se_mueven():
    # Aunque sus elementos sean Copy, arrays y tuplas se mueven.
    assert not is_copy(ArrayT(I32, 3))
    assert not is_copy(ArrayT(STRING, 3))
    assert not is_copy(TupleT((I32, BOOL)))
    assert not is_copy(TupleT((I32, STRING)))
    assert not is_copy(StructT("Punto"))
    assert not is_copy(EnumT("Estado"))


def test_str_de_tipos():
    assert str(ArrayT(I32, 3)) == "[i32; 3]"
    assert str(TupleT((I32, F64))) == "(i32, f64)"
    assert str(RefT(I32, mutable=True)) == "&mut i32"


def test_node_property():
    nodo = object()
    p = NodeProperty()
    assert p.get(nodo) is None
    p.put(nodo, I32)
    assert p.get(nodo) == I32 and nodo in p
    assert SemanticInfo().structs == {}
