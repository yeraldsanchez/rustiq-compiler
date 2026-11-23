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
  ;; si ocupan más. El Emitter cambia el valor inicial de $heap y el tamaño
  ;; inicial de la memoria (Emitter._heap_start); 1024 es el valor por defecto.
  
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
  ;; no se copian: se mueven.
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
  (func $f_suma_par (param $p_0 i32) (result i32)
    (local $tmp1 i32)
    (local $tmp2 i32)
    (local $a_1 i32)
    (local $tmp3 i32)
    (local $b_2 i32)
    local.get $p_0
    local.set $tmp1
    block $fin_match1 (result i32)
      block $sig_brazo2
        local.get $tmp1
        i32.load offset=0
        local.set $tmp2
        local.get $tmp2
        local.set $a_1
        local.get $tmp1
        i32.load offset=8
        local.set $tmp3
        local.get $tmp3
        local.set $b_2
        local.get $a_1
        local.get $b_2
        i32.add
        br $fin_match1
      end
      unreachable
    end
  )
  (func $f_intercambiar (param $p_3 i32) (result i32)
    (local $tmp1 i32)
    (local $tmp2 i32)
    (local $a_4 i32)
    (local $tmp3 i32)
    (local $b_5 i32)
    (local $tmp4 i32)
    local.get $p_3
    local.set $tmp1
    block $fin_match1 (result i32)
      block $sig_brazo2
        local.get $tmp1
        i32.load offset=0
        local.set $tmp2
        local.get $tmp2
        local.set $a_4
        local.get $tmp1
        i32.load offset=8
        local.set $tmp3
        local.get $tmp3
        local.set $b_5
        i32.const 16
        call $alloc
        local.set $tmp4
        local.get $tmp4
        local.get $b_5
        i32.store offset=0
        local.get $tmp4
        local.get $a_4
        i32.store offset=8
        local.get $tmp4
        br $fin_match1
      end
      unreachable
    end
  )
  (func $f_promedio (param $a_6 f64) (param $b_7 f64) (result f64)
    local.get $a_6
    local.get $b_7
    f64.add
    f64.const 2.0
    f64.div
  )
  (func $f_main (export "main")
    (local $par_8 i32)
    (local $tmp1 i32)
    (local $inv_9 i32)
    (local $tmp2 i32)
    (local $letra_10 i32)
    (local $mayor_11 i32)
    (local $r_12 i32)
    (local $tmp3 i32)
    (local $tmp4 i32)
    (local $tmp5 i32)
    (local $tmp6 i32)
    (local $tmp7 i32)
    (local $tmp8 i32)
    i32.const 16
    call $alloc
    local.set $tmp1
    local.get $tmp1
    i32.const 3
    i32.store offset=0
    local.get $tmp1
    i32.const 8
    i32.store offset=8
    local.get $tmp1
    local.set $par_8
    local.get $par_8
    call $f_suma_par
    call $print_i32
    i32.const 16
    call $alloc
    local.set $tmp2
    local.get $tmp2
    i32.const 3
    i32.store offset=0
    local.get $tmp2
    i32.const 8
    i32.store offset=8
    local.get $tmp2
    call $f_intercambiar
    local.set $inv_9
    local.get $inv_9
    call $f_suma_par
    call $print_i32
    f64.const 2.5
    f64.const 4.0
    call $f_promedio
    call $print_f64
    i32.const 82
    local.set $letra_10
    local.get $letra_10
    call $print_char
    f64.const 3.5
    f64.const 1.25
    f64.gt
    local.set $mayor_11
    local.get $mayor_11
    call $print_bool
    i32.const 16
    call $alloc
    local.set $tmp4
    local.get $tmp4
    i32.const 16
    call $alloc
    local.set $tmp5
    local.get $tmp5
    i32.const 3
    i32.store offset=0
    local.get $tmp5
    i32.const 8
    i32.store offset=8
    local.get $tmp5
    call $f_intercambiar
    call $f_suma_par
    i32.store offset=0
    local.get $tmp4
    local.get $mayor_11
    i32.store offset=8
    local.get $tmp4
    local.set $tmp3
    block $fin_match1 (result i32)
      block $sig_brazo2
        local.get $tmp3
        i32.load offset=0
        local.set $tmp6
        local.get $tmp6
        i32.const 11
        i32.ne
        br_if $sig_brazo2
        local.get $tmp3
        i32.load offset=8
        local.set $tmp7
        local.get $tmp7
        i32.const 1
        i32.ne
        br_if $sig_brazo2
        i32.const 1
        br $fin_match1
      end
      block $sig_brazo3
        local.get $tmp3
        i32.load offset=8
        local.set $tmp8
        local.get $tmp8
        i32.const 0
        i32.ne
        br_if $sig_brazo3
        i32.const 2
        br $fin_match1
      end
      block $sig_brazo4
        i32.const 3
        br $fin_match1
      end
      unreachable
    end
    local.set $r_12
    local.get $r_12
    call $print_i32
  )
)
