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
