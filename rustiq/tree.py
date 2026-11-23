"""Ayudas para recorrer el árbol de ANTLR, compartidas por la semántica y el codegen.

La gramática encadena una regla por nivel de precedencia, así que una expresión
simple como `x` llega envuelta en varios nodos de un solo hijo
(expression -> logicalOr -> ... -> postfix -> identP). Estas funciones quitan
esa envoltura sin que cada módulo repita el mismo ciclo.
"""

from antlr4 import ParserRuleContext

from rustiq.generated.RustiQParser import RustiQParser as P


def unwrap(node):
    """Un paso hacia adentro: el contenido de `( e )` o el único hijo regla del nodo.

    None si el nodo tiene operadores, sufijos o varios hijos.
    """
    if isinstance(node, P.ParenPContext):
        return node.expression()
    if node.getChildCount() == 1 and isinstance(node.getChild(0), ParserRuleContext):
        return node.getChild(0)
    return None


def split_call(primary, suffixes: list) -> tuple:
    """Separa la llamada directa `nombre(args)` de los demás sufijos de un `postfix`.

    Devuelve (sufijo de llamada, sufijos restantes) si `primary` es un nombre
    seguido de `(...)`, y si no (None, suffixes). Solo las llamadas por nombre
    son llamadas: `f(1)(2)` llama a `f` y el segundo `(2)` es un error.
    """
    if suffixes and isinstance(suffixes[0], P.CallSuffixContext) and isinstance(primary, P.IdentPContext):
        return suffixes[0], suffixes[1:]
    return None, suffixes
