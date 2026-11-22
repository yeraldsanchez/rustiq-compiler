# Interfaz entre los carriles A y B (Etapa 2)

Qué da el carril A (Yerald) y qué espera del carril B (Byron). Si algo de aquí cambia, se avisa y se actualiza en el mismo PR.

## Convención de los `visitX` de expresión

| Visitor | Qué hace un `visitX` de expresión |
| --- | --- |
| `Analyzer` | Devuelve su `Type`. Devuelve `None` si ya reportó un error que lo impide. Los errores en cascada se evitan con `self.mismatch(...)`, que calla cuando el tipo real es `None` |
| `Emitter` | Deja su valor en la pila de Wasm y no devuelve nada. Una expresión de tipo `()` no deja nada |

Los nodos de una cadena con un solo hijo (`expression` → `logicalOr` → … → `primary`) no necesitan `visitX`: el `visitChildren` por defecto propaga el valor devuelto.

## Qué provee A

### Ámbitos (`ScopeDefaults`, `semantic/scope_defaults.py`)

Implementación por defecto del contrato. `ScopesMixin` (B) la reemplaza al definir los mismos métodos.

```python
push_scope() / pop_scope()
declare(name, type, mutable, kind, node) -> Symbol | None   # None si ya existía (reporta E_REDECLARED)
lookup(name) -> Symbol | None
```

### `postfix` (espina compartida, en `analyzer.py` y `emitter.py`)

`visitPostfix` recorre `primary` y sus sufijos. Cada sufijo recibe el tipo de su operando en `info.expr_type.get(sufijo)`.

| Sufijo | Dueño |
| --- | --- |
| `visitCallSuffix` | A (solo `nombre(args)`) |
| `visitFieldSuffix` | A |
| `visitIndexSuffix` | **B**. En el Analyzer devuelve el tipo del elemento. En el Emitter encuentra la dirección del array en la pila |

### Emitter

| Método | Para qué |
| --- | --- |
| `load_symbol(symbol)` | Deja el valor de un símbolo en la pila. **`visitIdentP` debe usarlo.** Expande las constantes globales |
| `declare_symbol(symbol)` / `local_name(symbol)` | Declara un local y devuelve su nombre `$nombre_uid` |
| `new_temp(type)` / `new_label(prefix)` | Local temporal y etiqueta únicos dentro de la función |
| `field_slot(struct_type, campo)` | `(índice de ranura, tipo del campo)`. Sirve para asignar `p.x = ...` desde `place` |
| `wasm_type(type)` | `f64` para f64, `i32` para todo lo demás |

### Anotaciones que deja el Analyzer

| Clave | Valor |
| --- | --- |
| `info.symbol[parameter]`, `info.symbol[constDecl]`, `info.symbol[constLocalDecl]` | `Symbol` declarado |
| `info.expr_type[expresión de ExprStmt]` | Tipo, para que el Emitter descarte el valor |
| `info.expr_type[block]`, `[structLiteral]`, `[tupleLiteral]`, `[postfix]` | Tipo del nodo |
| `info.expr_type[sufijo]` | Tipo del **operando** del sufijo |
| `info.expr_type[enumValue]`, `[matchExpr]` | Tipo del nodo |
| `info.expr_type[matchExpr.condition()]` | Tipo del valor que examina el `match` |
| `info.expr_type[patrón]` | Tipo del valor contra el que se prueba ese patrón (también en subpatrones) |
| `info.symbol[bindingPat]` | `Symbol` del identificador que declara el patrón (inmutable, kind `"local"`) |

## Qué espera A de B

- `visitIdentP`: en el Analyzer anota `info.symbol[ctx]` y devuelve `symbol.type`. En el Emitter llama a `load_symbol`.
- `visitLetDecl` anota `info.symbol[ctx]` con el símbolo declarado.
- Los literales, operadores unarios y binarios cumplen la convención de arriba.
- Un parámetro se nombra por `uid` si `info.symbol[parameter]` existe. A lo llena en `visitFunctionDecl` con `declare(...)`.

### Movimientos (`semantic/moves.py`)

A ya lleva el estado de cada variable (disponible, movida, sin inicializar), las ramas (G8) y los ciclos. `visitIdentP` (Analyzer) ya llama a `check_use`, y `visitLetDecl` a `consume` y `track_symbol`. Una variable cuyo tipo quedó en `None` por un error previo no se mueve ni se reporta como sin inicializar, para no generar errores en cascada.

La asignación (`check_assign.py`) llama a `consume` y `mark_initialized`, y `visitArrayLiteral` (`check_arrays.py`) a `consume` por cada elemento.

`consume` ya consulta `is_borrowed(symbol)` (de `borrows.py`) y reporta `E_MOVE_WHILE_BORROWED`.

### Préstamos (`semantic/borrows.py`)

Un `&x` o `&mut x` crea un préstamo temporal que muere al terminar la sentencia (o la condición de `if`/`while`) que lo creó: `visitBlock` y `_check_condition` lo sueltan con `borrow_mark` y `release_temporary_borrows`. Si un `let` guarda una referencia, `keep_borrows` lo deja vivo hasta que `pop_scope` cierra ese ámbito.

## Pruebas

`tests/support.py` trae literales, identificadores, operadores, `let` y asignación simple **solo para probar el carril A**. Cuando B implemente `visitLiteral` en ambos visitors, `B_READY` pasa a `True` y se activan solas las pruebas que compilan los `.rq` completos.
