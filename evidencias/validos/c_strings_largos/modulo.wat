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
  (global $heap (mut i32) (i32.const 1224))
  
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
  (func $f_main (export "main")
    (local $s_0 i32)
    i32.const 0
    i32.const 100
    call $str_new
    call $print_str
    i32.const 100
    i32.const 100
    call $str_new
    call $print_str
    i32.const 200
    i32.const 100
    call $str_new
    call $print_str
    i32.const 300
    i32.const 100
    call $str_new
    call $print_str
    i32.const 400
    i32.const 100
    call $str_new
    call $print_str
    i32.const 500
    i32.const 100
    call $str_new
    call $print_str
    i32.const 600
    i32.const 100
    call $str_new
    call $print_str
    i32.const 700
    i32.const 100
    call $str_new
    call $print_str
    i32.const 800
    i32.const 100
    call $str_new
    call $print_str
    i32.const 900
    i32.const 100
    call $str_new
    call $print_str
    i32.const 1000
    i32.const 100
    call $str_new
    call $print_str
    i32.const 1100
    i32.const 100
    call $str_new
    call $print_str
    i32.const 1200
    i32.const 24
    call $str_new
    local.set $s_0
    local.get $s_0
    call $print_str
  )
  (data (i32.const 0) "\4c\69\6e\65\61\20\30\30\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 100) "\4c\69\6e\65\61\20\30\31\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 200) "\4c\69\6e\65\61\20\30\32\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 300) "\4c\69\6e\65\61\20\30\33\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 400) "\4c\69\6e\65\61\20\30\34\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 500) "\4c\69\6e\65\61\20\30\35\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 600) "\4c\69\6e\65\61\20\30\36\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 700) "\4c\69\6e\65\61\20\30\37\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 800) "\4c\69\6e\65\61\20\30\38\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 900) "\4c\69\6e\65\61\20\30\39\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 1000) "\4c\69\6e\65\61\20\31\30\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 1100) "\4c\69\6e\65\61\20\31\31\3a\20\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a\61\62\63\64\65\66\67\68\69\6a")
  (data (i32.const 1200) "\64\65\73\70\75\65\73\20\64\65\20\6c\6f\73\20\6c\69\74\65\72\61\6c\65\73")
)
