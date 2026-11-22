(module
  (import "env" "print_i32" (func $print_i32 (param i32)))
  (import "env" "print_f64" (func $print_f64 (param f64)))
  (import "env" "print_bool" (func $print_bool (param i32)))
  (import "env" "print_char" (func $print_char (param i32)))
  (import "env" "print_str" (func $print_str (param i32)))
  (memory (export "memory") 1)
  ;; Mapa de la memoria lineal:
  ;;   [0, fin de los literales)  datos estáticos: los literales de String (segmentos `data`)
  ;;   [inicio del heap, ...)     heap, crece hacia arriba y nunca se libera
  ;; El heap empieza en 1024, o justo después de los literales (redondeado a 8)
  ;; si ocupan más. El Emitter reescribe el valor inicial de $heap y el tamaño
  ;; inicial de la memoria (Emitter._place_heap); 1024 es el valor por defecto.
  
  ;; Siguiente dirección libre del heap. Solo avanza.
  (global $heap (mut i32) (i32.const 1024))
  
  ;; Reserva `n` bytes en el heap y devuelve la dirección del bloque.
  ;; Redondea `n` a múltiplo de 8 para que todo bloque quede alineado a 8,
  ;; igual que las ranuras de structs, tuplas, arrays y enums.
  ;; Si el bloque no cabe, pide las páginas que falten con memory.grow.
  (func $alloc (param $n i32) (result i32)
    (local $ptr i32)
    (local $end i32)
    (local $limit i32)
    (local.set $ptr (global.get $heap))
    ;; end = ptr + ((n + 7) & ~7)
    (local.set $end
      (i32.add
        (local.get $ptr)
        (i32.and (i32.add (local.get $n) (i32.const 7)) (i32.const -8))))
    ;; limit = páginas actuales * 64 KiB
    (local.set $limit (i32.shl (memory.size) (i32.const 16)))
    (if (i32.gt_u (local.get $end) (local.get $limit))
      (then
        ;; páginas que faltan = ceil((end - limit) / 64 KiB)
        (if (i32.eq
              (memory.grow
                (i32.shr_u
                  (i32.add
                    (i32.sub (local.get $end) (local.get $limit))
                    (i32.const 65535))
                  (i32.const 16)))
              (i32.const -1))
          (then unreachable))))
    (global.set $heap (local.get $end))
    (local.get $ptr))
  
  ;; Copia `n` bytes de `src` a `dst`, byte por byte.
  ;; Se usa para crear Strings a partir de sus literales. Arrays y tuplas
  ;; no se copian: se mueven (G1).
  ;; Los bloques del bump allocator nunca se solapan, así que copiar hacia
  ;; adelante basta.
  (func $memcpy (param $dst i32) (param $src i32) (param $n i32)
    (local $i i32)
    (block $fin
      (loop $siguiente
        (br_if $fin (i32.ge_u (local.get $i) (local.get $n)))
        (i32.store8
          (i32.add (local.get $dst) (local.get $i))
          (i32.load8_u (i32.add (local.get $src) (local.get $i))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $siguiente))))
  
  ;; Crea un String en el heap a partir de `len` bytes UTF-8 en `src`
  ;; (normalmente un literal en la zona estática).
  ;; Layout: [len: i32][bytes UTF-8]. Devuelve el puntero al inicio.
  (func $str_new (param $src i32) (param $len i32) (result i32)
    (local $s i32)
    (local.set $s (call $alloc (i32.add (i32.const 4) (local.get $len))))
    (i32.store (local.get $s) (local.get $len))
    (call $memcpy
      (i32.add (local.get $s) (i32.const 4))
      (local.get $src)
      (local.get $len))
    (local.get $s))
  
  ;; Largo en bytes de un String.
  (func $str_len (param $s i32) (result i32)
    (i32.load (local.get $s)))
  
  ;; Dirección del primer byte de un String.
  (func $str_data (param $s i32) (result i32)
    (i32.add (local.get $s) (i32.const 4)))
  (func $f_tick (param $c_0 i32) (result i32)
    local.get $c_0
    i32.load
    i32.const 1
    i32.add
  )
  (func $f_sumar (param $c_1 i32) (result i32)
    local.get $c_1
    i32.const 0
    i32.add
    local.get $c_1
    i32.load offset=0
    i32.const 1
    i32.add
    i32.store
    local.get $c_1
    i32.load offset=0
  )
  (func $f_mostrar (param $a_2 i32) (param $b_3 i32)
    local.get $a_2
    call $print_i32
    local.get $b_3
    call $print_i32
  )
  (func $f_main (export "main")
    (local $c_4_cell i32)
    (local $c_4 i32)
    (local $k_5 i32)
    (local $tmp1 i32)
    i32.const 8
    call $alloc
    local.set $c_4_cell
    local.get $c_4_cell
    i32.const 5
    i32.store
    local.get $c_4_cell
    call $f_tick
    local.get $c_4_cell
    call $f_tick
    i32.add
    call $print_i32
    i32.const 8
    call $alloc
    local.set $tmp1
    local.get $tmp1
    i32.const 0
    i32.store offset=0
    local.get $tmp1
    local.set $k_5
    local.get $k_5
    call $f_sumar
    local.get $k_5
    call $f_sumar
    call $f_mostrar
    local.get $k_5
    i32.load offset=0
    call $print_i32
  )
)
