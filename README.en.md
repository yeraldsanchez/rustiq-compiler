# 🦀 RustiQ

[Español](README.md) · **English**

**Write Rust. Run it in the browser.**

> 👉 **Try it without installing anything at [rustiq.yeraldsanchez.dev](https://rustiq.yeraldsanchez.dev).**

RustiQ is a compiler that takes a subset of Rust and turns it into **WebAssembly**, with a web editor to write, compile and run your code instantly, with nothing to install.

## ✨ Features

- **A familiar language:** functions, structs, enums, tuples, arrays, `match`, type inference and explicit mutability.
- **Rust-style safety:** ownership, moves and borrows (`&` / `&mut`) checked at compile time. If you use a value after moving it, the compiler tells you.
- **Clear errors:** every error points to the exact line and column and is underlined right in the editor.
- **Real WebAssembly:** the output is a validated `.wasm` module, along with its readable WAT version.
- **In-browser editor:** write, compile and see the output on the same screen. It has a side rail with file, outline and example panels, tabs, a start screen with recently closed files, quick fixes for common errors, go to definition (F12), references (Shift+F12) and rename (F2).

The compiler's error messages and the editor's interface are in Spanish.

## 🧪 A quick look

```rust
struct Point {
    x: i32,
    y: i32,
}

fn sum(p: Point) -> i32 {
    p.x + p.y
}

fn main() {
    let p = Point { x: 3, y: 4 };
    print_i32(sum(p));
}
```

And if you try to use `p` again after passing it to `sum`, the compiler stops you with a use-after-move error, just like Rust.

## ⚙️ How it works

```
Your code  →  Parsing  →  Type and ownership checking  →  WebAssembly  →  Execution
```

Built with Python, ANTLR4, FastAPI and CodeMirror.

## 🚀 Getting started

### With Docker (fastest)

All you need is [Docker](https://docs.docker.com/get-docker/). The image includes Python, wabt and the prebuilt editor:

```bash
docker build -t rustiq .
docker run --rm -p 8000:8000 rustiq
```

Or with Compose: `docker compose up --build`.

The editor is at `http://localhost:8000/` and the API at `POST http://localhost:8000/compile`. To run the tests inside the image: `docker run --rm rustiq python -m pytest`.

### System requirements

These tools are not installed with pip:

| Tool | What for | Installation |
| --- | --- | --- |
| Python 3.12 | The whole compiler | [uv](https://docs.astral.sh/uv/) downloads it for you |
| wabt | `wat2wasm` and `wasm-validate` | Linux/macOS: `sudo pacman -S wabt`, `sudo apt install wabt` or `brew install wabt`. Windows: see below |
| Java 11 or later | Only to regenerate the grammar with ANTLR | Linux: `sudo pacman -S jre-openjdk-headless` or `sudo apt install default-jre-headless`. Windows: see below |

#### Windows

wabt has no official Windows installer. There are two ways:

- **Scoop** (simplest): `scoop install wabt`
- **Manual:** download the Windows `.zip` from [the wabt releases](https://github.com/WebAssembly/wabt/releases), extract it (for example to `C:\tools\wabt`) and add its `bin` folder to the `PATH`. Then open a new terminal.

To check that it is on the `PATH`:

```powershell
where.exe wat2wasm
wat2wasm --version
```

Java (only to regenerate the grammar): `winget install EclipseAdoptium.Temurin.21.JRE`.

uv: `winget install astral-sh.uv` or `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`.

### Installation

From the project folder, with [uv](https://docs.astral.sh/uv/) (recommended). If you don't have the folder, clone the repository with `git clone https://github.com/yeraldsanchez/rustiq-compiler`:

```bash
cd rustiq-compiler
uv sync
source .venv/bin/activate      # in fish: source .venv/bin/activate.fish
```

On Windows (PowerShell), activate the venv with `.venv\Scripts\Activate.ps1`. If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once. In `cmd` it is `.venv\Scripts\activate.bat`.

Without uv:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows without uv: `py -3.12 -m venv .venv`, activate it as above and then `pip install -r requirements.txt`.

### Verify the installation

```bash
wat2wasm --version
wasm-validate --version
python --version               # 3.12.x
python -m pytest
```

### Generate the evidence

```bash
python -m scripts.evidencias
```

Compiles every program in `tests/valid` and `tests/invalid` and writes `evidencias/`: for each valid program, its `.wat`, its `.wasm`, the `wasm-validate` output and the execution output; for each invalid one, the error it gives and that no module was produced. `evidencias/RESUMEN.md` puts it all together in a table.

### Run the server

```bash
uvicorn server.app:app --reload
```

The API is at `POST http://localhost:8000/compile` and the editor at `http://localhost:8000/`. The interactive documentation (`/docs`) is enabled with `RUSTIQ_DOCS=1 uvicorn server.app:app --reload`; without that variable it is not published.

The server sends no CORS headers: the editor and the API share an origin, so no other site can use the compiler from its visitors' browsers. If you need to open the editor from another origin, put the origins, comma-separated, in `RUSTIQ_CORS_ORIGINS` (for example, `RUSTIQ_CORS_ORIGINS=http://localhost:3000`). `npm run dev` doesn't need it, because Vite forwards `/compile` and the browser sees a single origin.

### Working on the editor

The editor lives in `web/`, written in TypeScript with Vite and CodeMirror 6. What FastAPI serves is `web/dist/`, which comes prebuilt in the repo: you don't need Node to use the editor. You only need Node 20 or later to change it:

```bash
cd web
npm install
npm run dev        # http://localhost:5173, forwards /compile to uvicorn on port 8000
npm run build      # type-checks and regenerates web/dist/
```

After changing anything in `web/src/`, `web/index.html` or `web/styles.css`, run `npm run build` and commit `web/dist/` in the same commit.

### Regenerate the grammar

The ANTLR files are already in `rustiq/generated/`, so Java is only needed if you edit `grammar/RustiQ.g4`:

```bash
antlr4 -v 4.13.2 -Dlanguage=Python3 -visitor -no-listener -Xexact-output-dir -o rustiq/generated grammar/RustiQ.g4
```

The tool version must match the runtime version (`antlr4-python3-runtime==4.13.2`).

### Update dependencies

Edit `pyproject.toml` (or run `uv add <package>`) and regenerate the file used by CI:

```bash
uv export --no-hashes -o requirements.txt
```

Commit `pyproject.toml`, `uv.lock` and `requirements.txt` together.

## 📚 Documentation

These documents are in Spanish:

- [`docs/decisiones.md`](docs/decisiones.md): what is supported, what is partial, what is not supported and how RustiQ differs from Rust.
- [`docs/memoria.md`](docs/memoria.md): in-memory representation of `String`, arrays, tuples, structs, enums and references.
- [`tests/README.md`](tests/README.md): format of the valid and invalid test programs.
- [`evidencias/RESUMEN.md`](evidencias/RESUMEN.md): result of compiling, validating and running each test program.
