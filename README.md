# 🦀 RustiQ

**Escribe Rust. Ejecútalo en el navegador.**

RustiQ es un compilador que toma un subconjunto de Rust y lo convierte en **WebAssembly**, con un editor web para escribir, compilar y ejecutar tu código al instante, sin instalar nada.

## ✨ Qué ofrece

- **Un lenguaje familiar:** funciones, structs, enums, tuplas, arrays, `match`, inferencia de tipos y mutabilidad explícita.
- **Seguridad al estilo Rust:** ownership, movimientos y préstamos (`&` / `&mut`) verificados en tiempo de compilación. Si usas un valor después de moverlo, el compilador te lo dice.
- **Errores claros:** cada error indica la línea y la columna exactas y se subraya directamente en el editor.
- **WebAssembly real:** el resultado es un módulo `.wasm` validado, junto con su versión legible en WAT.
- **Editor en el navegador:** escribe, compila y mira la salida en la misma pantalla. Tiene un riel lateral con paneles de archivos, esquema y ejemplos, pestañas, una pantalla de inicio con los archivos cerrados hace poco, arreglos rápidos para los errores comunes, ir a la definición (F12), referencias (Shift+F12) y renombrar (F2).

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

### Con Docker (lo más rápido)

Solo hace falta [Docker](https://docs.docker.com/get-docker/). La imagen trae Python, wabt y el editor ya construido:

```bash
docker build -t rustiq .
docker run --rm -p 8000:8000 rustiq
```

O con Compose: `docker compose up --build`.

El editor queda en `http://localhost:8000/` y la API en `POST http://localhost:8000/compile`. Para correr las pruebas dentro de la imagen: `docker run --rm rustiq python -m pytest`.

### Requisitos del sistema

Estas herramientas no se instalan con pip:

| Herramienta | Para qué | Instalación |
| --- | --- | --- |
| Python 3.12 | Todo el compilador | [uv](https://docs.astral.sh/uv/) lo descarga solo |
| wabt | `wat2wasm` y `wasm-validate` | Linux/macOS: `sudo pacman -S wabt`, `sudo apt install wabt` o `brew install wabt`. Windows: ver abajo |
| Java 11 o superior | Solo para regenerar la gramática con ANTLR | Linux: `sudo pacman -S jre-openjdk-headless` o `sudo apt install default-jre-headless`. Windows: ver abajo |

#### Windows

wabt no tiene instalador oficial de Windows. Hay dos caminos:

- **Scoop** (más simple): `scoop install wabt`
- **Manual:** descargar el `.zip` de Windows desde [las releases de wabt](https://github.com/WebAssembly/wabt/releases), descomprimirlo (por ejemplo en `C:\tools\wabt`) y agregar su carpeta `bin` al `PATH`. Después se abre una terminal nueva.

Para comprobar que quedó en el `PATH`:

```powershell
where.exe wat2wasm
wat2wasm --version
```

Java (solo si se va a regenerar la gramática): `winget install EclipseAdoptium.Temurin.21.JRE`.

uv: `winget install astral-sh.uv` o `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`.

### Instalación

Desde la carpeta del proyecto, con [uv](https://docs.astral.sh/uv/) (recomendado). Si no se tiene la carpeta, se puede clonar el repositorio con `git clone https://github.com/yeraldsanchez/rustiq-compiler`:

```bash
cd rustiq-compiler
uv sync
source .venv/bin/activate      # en fish: source .venv/bin/activate.fish
```

En Windows (PowerShell), el venv se activa con `.venv\Scripts\Activate.ps1`. Si PowerShell bloquea el script, se ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. En `cmd` es `.venv\Scripts\activate.bat`.

Sin uv:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Windows sin uv: `py -3.12 -m venv .venv`, se activa como arriba y luego `pip install -r requirements.txt`.

### Verificar la instalación

```bash
wat2wasm --version
wasm-validate --version
python --version               # 3.12.x
python -m pytest
```

### Generar las evidencias

```bash
python -m scripts.evidencias
```

Compila todos los programas de `tests/valid` y `tests/invalid` y escribe `evidencias/`: por cada programa válido, su `.wat`, su `.wasm`, la salida de `wasm-validate` y la salida de la ejecución; por cada inválido, el error que da y que no produjo módulo. `evidencias/RESUMEN.md` junta todo en una tabla.

### Levantar el servidor

```bash
uvicorn server.app:app --reload
```

La API queda en `POST http://localhost:8000/compile` y el editor en `http://localhost:8000/`. La documentación interactiva está en `/docs`.

### Trabajar en el editor

El editor está en `web/`, escrito en TypeScript con Vite y CodeMirror 6. Lo que sirve FastAPI es `web/dist/`, que ya viene construido en el repo: para usar el editor no hace falta Node. Solo se necesita Node 20 o superior para modificarlo:

```bash
cd web
npm install
npm run dev        # http://localhost:5173, reenvía /compile a uvicorn en el puerto 8000
npm run build      # revisa los tipos y regenera web/dist/
```

Después de cambiar algo en `web/src/`, `web/index.html` o `web/styles.css` hay que correr `npm run build` y subir `web/dist/` en el mismo commit.

### Regenerar la gramática

Los archivos de ANTLR ya están en `rustiq/generated/`, así que Java solo hace falta si se edita `grammar/RustiQ.g4`:

```bash
antlr4 -v 4.13.2 -Dlanguage=Python3 -visitor -no-listener -Xexact-output-dir -o rustiq/generated grammar/RustiQ.g4
```

La versión de la herramienta debe coincidir con la del runtime (`antlr4-python3-runtime==4.13.2`).

### Actualizar dependencias

Se edita `pyproject.toml` (o `uv add <paquete>`) y se regenera el archivo para CI:

```bash
uv export --no-hashes -o requirements.txt
```

Se suben `pyproject.toml`, `uv.lock` y `requirements.txt` juntos.


## 📚 Documentación

- [`docs/decisiones.md`](docs/decisiones.md): qué se soporta, qué es parcial, qué no se soporta y en qué se diferencia RustiQ de Rust.
- [`docs/memoria.md`](docs/memoria.md): representación en memoria de `String`, arrays, tuplas, structs, enums y referencias.
- [`tests/README.md`](tests/README.md): formato de los programas de prueba válidos e inválidos.
- [`evidencias/RESUMEN.md`](evidencias/RESUMEN.md): resultado de compilar, validar y ejecutar cada programa de prueba.
