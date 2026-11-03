# 🦀 RustiQ

**Escribe Rust. Ejecútalo en el navegador.**

RustiQ es un compilador que toma un subconjunto de Rust y lo convierte en **WebAssembly**, con un editor web para escribir, compilar y ejecutar tu código al instante, sin instalar nada.

> 🚧 En desarrollo activo.

## ✨ Qué ofrece

- **Un lenguaje familiar:** funciones, structs, enums, tuplas, arrays, `match`, inferencia de tipos y mutabilidad explícita.
- **Seguridad al estilo Rust:** ownership, movimientos y préstamos (`&` / `&mut`) verificados en tiempo de compilación. Si usas un valor después de moverlo, el compilador te lo dice.
- **Errores claros:** cada error indica la línea y la columna exactas y se subraya directamente en el editor.
- **WebAssembly real:** el resultado es un módulo `.wasm` validado, junto con su versión legible en WAT.
- **Editor en el navegador:** escribe, compila y mira la salida en la misma pantalla.

## 🧪 Un vistazo

```rust
struct Punto {
    x: i32,
    y: i32,
}

fn suma(p: Punto) -> i32 {
    p.x + p.y
}

fn main() {
    let p = Punto { x: 3, y: 4 };
    print_i32(suma(p));
}
```

Y si intentas usar `p` otra vez después de pasarlo a `suma`, el compilador lo detiene con un error de uso después de movimiento, igual que Rust.

## ⚙️ Cómo funciona

```
Tu código  →  Análisis  →  Verificación de tipos y ownership  →  WebAssembly  →  Ejecución
```

Hecho con Python, ANTLR4, FastAPI y CodeMirror.

## 🚀 Empezar

Las instrucciones de instalación y uso se agregarán pronto.

