# Evidencias de compilación, validación y ejecución

Generado con `python -m scripts.evidencias` el 2026-11-22 15:50.

Herramientas: wat2wasm 1.0.42; wasm-validate 1.0.42; Python 3.12.15

## Programas válidos

Cada carpeta de `validos/` tiene el fuente, el `.wat`, el `.wasm`, la salida de `wasm-validate` y la salida de la ejecución con wasmtime.

| Programa | Compila | wasm-validate | Ejecuta | Salida = esperada |
| --- | --- | --- | --- | --- |
| b_str_escapes | sí | sí | sí | sí |
| c_bloque_anidado_final | sí | sí | sí | sí |
| c_escapes_y_comentarios | sí | sí | sí | sí |
| c_imprimir_string_dos_veces | sí | sí | sí | sí |
| c_inicializar_en_ramas | sí | sí | sí | sí |
| c_leer_partes | sí | sí | sí | sí |
| c_leer_tras_prestamo_mutable | sí | sí | sí | sí |
| c_limites_i32 | sí | sí | sí | sí |
| c_match_con_return | sí | sí | sí | sí |
| c_mover_campo_propio | sí | sí | sí | sí |
| c_nombres_del_runtime | sí | sí | sí | sí |
| c_prestamos_en_argumentos | sí | sí | sí | sí |
| c_referencia_asignada | sí | sí | sí | sí |
| c_retornar_ref_recibida | sí | sí | sí | sí |
| c_strings_largos | sí | sí | sí | sí |
| c_struct_en_condicion | sí | sí | sí | sí |
| control_flujo | sí | sí | sí | sí |
| ejemplo_gramatica | sí | sí | sí | sí |
| enums_match | sí | sí | sí | sí |
| funciones_const | sí | sí | sí | sí |
| print_str_basic | sí | sí | sí | sí |
| structs_basico | sí | sí | sí | sí |
| test_b1_expresiones | sí | sí | sí | sí |
| test_b2_ambitos | sí | sí | sí | sí |
| test_b3_arrays | sí | sí | sí | sí |
| test_b4_strings | sí | sí | sí | sí |
| test_b5_referencias | sí | sí | sí | sí |
| tuplas_tipos | sí | sí | sí | sí |

## Programas inválidos

Cada uno debe fallar con el error de su cabecera `// ERROR` y no producir módulo.

| Programa | Primer error | Error = esperado | Sin módulo |
| --- | --- | --- | --- |
| a_argumentos_de_mas | `semantico E_ARG_COUNT 3:13` 'dos' espera 0 argumento(s) y recibió 2 | sí | sí |
| a_argumentos_de_menos | `semantico E_ARG_COUNT 5:13` 'suma' espera 2 argumento(s) y recibió 1 | sí | sí |
| a_break_fuera_de_ciclo | `semantico E_BREAK_OUTSIDE_LOOP 3:5` 'break' solo puede usarse dentro de while o loop | sí | sí |
| a_continue_fuera_de_ciclo | `semantico E_BREAK_OUTSIDE_LOOP 5:9` 'continue' solo puede usarse dentro de while o loop | sí | sí |
| a_enum_datos_de_mas | `semantico E_ARG_COUNT 4:5` 'Forma::Punto' espera 0 dato(s) y recibió 1 | sí | sí |
| a_enum_variante_inexistente | `semantico E_UNKNOWN_VARIANT 4:12` 'Forma' no tiene la variante 'Circulo' | sí | sí |
| a_funcion_duplicada | `semantico E_REDECLARED 3:4` La función 'f' ya fue declarada | sí | sí |
| a_funcion_inexistente | `semantico E_UNDECLARED 4:5` La función 'nada' no existe | sí | sí |
| a_main_con_parametros | `semantico E_BAD_MAIN 2:4` 'main' no recibe parámetros ni devuelve valor | sí | sí |
| a_match_brazos_distintos | `semantico E_TYPE_MISMATCH 8:14` El brazo de match: se esperaba Forma y se encontró Color | sí | sí |
| a_match_no_exhaustivo | `semantico E_NOT_EXHAUSTIVE 6:5` El match sobre Forma no cubre todos los casos; agrega un brazo '_' | sí | sí |
| a_mover_dentro_de_ciclo | `semantico E_USE_AFTER_MOVE 6:14` 'p' se declaró fuera del ciclo y se movería en cada vuelta | sí | sí |
| a_mover_en_una_rama | `semantico E_USE_AFTER_MOVE 10:10` 'a' se usó después de moverse | sí | sí |
| a_mover_prestado | `semantico E_MOVE_WHILE_BORROWED 7:10` 'a' no se puede mover mientras está prestado | sí | sí |
| a_mover_string_dos_veces | `semantico E_USE_AFTER_MOVE 5:15` 's' se usó después de moverse | sí | sí |
| a_patron_variante_inexistente | `semantico E_UNKNOWN_VARIANT 7:16` 'Forma' no tiene la variante 'Circulo' | sí | sí |
| a_retorno_faltante | `semantico E_BAD_RETURN 4:1` 'valor' debe devolver i32 en todos sus caminos | sí | sí |
| a_return_sin_valor | `semantico E_BAD_RETURN 3:5` Se debe devolver un valor de tipo i32 | sí | sí |
| a_sin_main | `semantico E_BAD_MAIN 2:1` Falta la función 'main' | sí | sí |
| a_struct_campo_faltante | `semantico E_MISSING_FIELD 5:13` Faltan campos en 'Punto': y | sí | sí |
| a_struct_campo_inexistente | `semantico E_UNKNOWN_FIELD 4:27` 'Punto' no tiene el campo 'z' | sí | sí |
| a_struct_duplicado | `semantico E_REDECLARED 3:8` El tipo 'S' ya fue declarado | sí | sí |
| a_struct_inexistente | `semantico E_UNKNOWN_TYPE 3:13` El struct 'Nada' no existe | sí | sí |
| a_tipo_desconocido | `semantico E_UNKNOWN_TYPE 2:17` El tipo 'Fantasma' no existe | sí | sí |
| a_uso_despues_de_mover | `semantico E_USE_AFTER_MOVE 7:10` 'a' se usó después de moverse | sí | sí |
| a_uso_sin_inicializar | `semantico E_UNINITIALIZED 6:10` 'a' se usó antes de asignarle un valor | sí | sí |
| b_asignar_prestado | `semantico E_ASSIGN_WHILE_BORROWED 5:5` No se puede asignar a 'x' mientras está prestado | sí | sí |
| b_retornar_ref_local | `semantico E_RETURN_LOCAL_REF 4:5` No se puede devolver una referencia a un valor local | sí | sí |
| c_bloque_sentencia_con_valor | `semantico E_TYPE_MISMATCH 4:9` Un bloque usado como sentencia no puede producir un valor (i32); agrega ';' o usa return | sí | sí |
| c_caracter_no_valido | `lexico E_INVALID_CHAR 3:15` Carácter no válido: '#' | sí | sí |
| c_char_de_varios | `lexico E_INVALID_CHAR 3:13` Un literal char lleva exactamente un carácter | sí | sí |
| c_comentario_sin_cerrar | `lexico E_UNTERMINATED_COMMENT 4:1` Comentario de bloque sin cerrar: falta '*/' | sí | sí |
| c_dos_mut_en_una_llamada | `semantico E_BORROW_CONFLICT 6:19` 'c' ya está prestado y no puede recibir &mut | sí | sí |
| c_escape_invalido | `lexico E_INVALID_ESCAPE 3:19` Secuencia de escape no válida '\q'; se aceptan \n, \t, \r, \\, \" y \' | sí | sí |
| c_inicializar_sin_else | `semantico E_UNINITIALIZED 7:15` 'x' se usó antes de asignarle un valor | sí | sí |
| c_leer_con_prestamo_mutable | `semantico E_BORROW_CONFLICT 10:15` 'p' tiene un préstamo mutable activo y no se puede usar hasta que termine | sí | sí |
| c_literal_enorme | `semantico E_INT_OUT_OF_RANGE 3:15` El literal 99999999999 no cabe en i32 (de -2147483648 a 2147483647) | sí | sí |
| c_literal_fuera_de_i32 | `semantico E_INT_OUT_OF_RANGE 3:13` El literal 2147483648 no cabe en i32 (de -2147483648 a 2147483647) | sí | sí |
| c_match_sobre_unit | `semantico E_TYPE_MISMATCH 5:11` El valor de match no puede ser '()'; la expresión no produce un valor | sí | sí |
| c_match_un_brazo_sin_return | `semantico E_BAD_RETURN 11:1` 'f' debe devolver i32 en todos sus caminos | sí | sí |
| c_mover_campo | `semantico E_USE_AFTER_MOVE 16:15` 'f' se usó después de moverse | sí | sí |
| c_mover_desde_referencia | `semantico E_MOVE_OUT_OF_PLACE 7:11` No se puede mover '*r' (String) fuera de una referencia; usa '&' para prestarlo | sí | sí |
| c_mover_desde_referencia_campo | `semantico E_MOVE_OUT_OF_PLACE 9:11` No se puede mover '(&c).s' (String) fuera de una referencia; usa '&' para prestarlo | sí | sí |
| c_mover_dos_veces_en_llamada | `semantico E_USE_AFTER_MOVE 6:15` 's' se usó después de moverse | sí | sí |
| c_mover_dos_veces_en_struct | `semantico E_USE_AFTER_MOVE 9:28` 's' se usó después de moverse | sí | sí |
| c_mover_dos_veces_en_tupla | `semantico E_USE_AFTER_MOVE 4:17` 's' se usó después de moverse | sí | sí |
| c_mover_elemento | `semantico E_USE_AFTER_MOVE 7:15` 'a' se usó después de moverse | sí | sí |
| c_prestar_unit | `semantico E_TYPE_MISMATCH 5:14` Lo que se presta con '&' no puede ser '()'; la expresión no produce un valor | sí | sí |
| c_referencia_colgante | `semantico E_DANGLING_REF 6:14` 'x' no vive lo suficiente: muere al cerrar su bloque y 'r' lo seguiría usando | sí | sí |
| c_referencia_colgante_reasignada | `semantico E_DANGLING_REF 7:14` 'y' no vive lo suficiente: muere al cerrar su bloque y 'r' lo seguiría usando | sí | sí |
| c_retornar_ref_local_por_llamada | `semantico E_RETURN_LOCAL_REF 8:5` No se puede devolver una referencia a un valor local | sí | sí |
| c_retornar_ref_local_por_match | `semantico E_RETURN_LOCAL_REF 4:5` No se puede devolver una referencia a un valor local | sí | sí |
| c_string_sin_cerrar | `lexico E_UNTERMINATED_STRING 3:15` String sin cerrar: falta la comilla '"' antes del fin de la línea | sí | sí |
| c_struct_suelto_en_condicion | `sintactico E_SYNTAX 7:8` Error: no viable alternative at input 'Punto' | sí | sí |
| c_unit_en_array | `semantico E_TYPE_MISMATCH 5:14` Un elemento de array no puede ser '()'; la expresión no produce un valor | sí | sí |
| c_unit_en_tupla | `semantico E_TYPE_MISMATCH 5:14` Un elemento de tupla no puede ser '()'; la expresión no produce un valor | sí | sí |
