"""Generación de código de referencias (`&`, `&mut`, `*`) y Strings (Carril B)."""

from rustiq.generated.RustiQParser import RustiQParser
from rustiq.semantic.info import Symbol
from rustiq.types import BOOL, CHAR, F64, I32, RefT, Type

SCALAR_TYPES = (I32, F64, BOOL, CHAR)


def _decode_rustiq_string(raw_literal: str) -> bytes:
    """Convierte el texto de un STRING_LIT (con comillas y escapes) a bytes UTF-8."""
    inner = raw_literal[1:-1]
    out: list[str] = []
    i = 0
    escapes = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "'": "'", "\\": "\\"}
    while i < len(inner):
        if inner[i] == "\\" and i + 1 < len(inner):
            out.append(escapes.get(inner[i + 1], inner[i + 1]))
            i += 2
        else:
            out.append(inner[i])
            i += 1
    return "".join(out).encode("utf-8")


def _format_wat_bytes(data: bytes) -> str:
    """Formatea bytes UTF-8 como literal de segmento `(data ...)` en WAT."""
    parts: list[str] = []
    for b in data:
        if 32 <= b <= 126 and b not in (34, 92):
            parts.append(chr(b))
        else:
            parts.append(f"\\{b:02x}")
    return '"' + "".join(parts) + '"'


class RefsGenMixin:
    def _string_segments(self) -> list[tuple[int, bytes]]:
        return self.__dict__.setdefault("_data_segments", [])

    def _next_data_offset(self) -> int:
        return self.__dict__.get("_data_offset", 0)

    def emit_string_literal(self, raw_literal: str) -> None:
        """Coloca los bytes UTF-8 en la zona estática [0, 1024) y llama a `$str_new`."""
        data = _decode_rustiq_string(raw_literal)
        offset = self._next_data_offset()
        self._data_offset = offset + len(data)
        self._string_segments().append((offset, data))

        self.emit(f"i32.const {offset}")
        self.emit(f"i32.const {len(data)}")
        self.emit("call $str_new")

    def emit_data_sections(self) -> list[str]:
        """Devuelve las líneas `(data (i32.const offset) "...")` registradas en el módulo."""
        return [
            f"  (data (i32.const {offset}) {_format_wat_bytes(data)})"
            for offset, data in self._string_segments()
        ]

    # ---------------------------------------------------------------
    # Celdas de heap para escalares con `address_taken`
    # ---------------------------------------------------------------

    @staticmethod
    def is_boxed_scalar(symbol: Symbol) -> bool:
        return symbol.address_taken and symbol.type in SCALAR_TYPES

    def emit_box_alloc(self, symbol: Symbol) -> None:
        """Reserva 8 bytes en el heap y guarda la dirección en el local del símbolo."""
        lname = self.declare_symbol(symbol)
        self.emit("i32.const 8")
        self.emit("call $alloc")
        self.emit(f"local.set {lname}")

    def emit_box_store(self, symbol: Symbol) -> None:
        """Asume que el valor escalar está en el tope de la pila; lo guarda en su celda."""
        lname = self.local_name(symbol)
        tmp = self.new_temp(symbol.type)
        self.emit(f"local.set {tmp}")
        self.emit(f"local.get {lname}")
        self.emit(f"local.get {tmp}")
        self.emit("f64.store" if symbol.type == F64 else "i32.store")

    def emit_box_load(self, symbol: Symbol) -> None:
        """Carga el valor escalar desde su celda en el heap hacia la pila."""
        lname = self.local_name(symbol)
        self.emit(f"local.get {lname}")
        self.emit("f64.load" if symbol.type == F64 else "i32.load")

    # ---------------------------------------------------------------
    # Operadores `&`, `&mut` y `*`
    # ---------------------------------------------------------------

    def emit_borrow(self, ctx: RustiQParser.UnaryContext) -> None:
        """Deja en la pila la dirección de memoria del operando."""
        postfix = ctx.postfix()
        primary = postfix.primary()
        suffixes = postfix.children[1:]

        if not suffixes and isinstance(primary, RustiQParser.IdentPContext):
            symbol = self.info.symbol.get(primary)
            if symbol is not None and self.is_boxed_scalar(symbol):
                self.emit(f"local.get {self.local_name(symbol)}")
                return
            self.visit(postfix)
            return

        self.visit(primary)
        current_type: Type | None = self.info.expr_type.get(suffixes[0]) if suffixes else None
        for idx, suffix in enumerate(suffixes):
            if isinstance(current_type, RefT):
                current_type = current_type.target
            if isinstance(suffix, RustiQParser.FieldSuffixContext):
                slot_idx, field_type = self.field_slot(current_type, suffix.IDENT().getText())
                if slot_idx > 0:
                    self.emit(f"i32.const {slot_idx * 8}")
                    self.emit("i32.add")
                if idx < len(suffixes) - 1:
                    self.emit("i32.load")
                current_type = field_type
            elif isinstance(suffix, RustiQParser.IndexSuffixContext):
                self.visit(suffix.expression())
                self.emit("i32.const 8")
                self.emit("i32.mul")
                self.emit("i32.add")
                if idx < len(suffixes) - 1:
                    self.emit("i32.load")
                current_type = current_type.elem

    def emit_deref(self, ctx: RustiQParser.UnaryContext) -> None:
        """Evalúa `*postfix` leyendo el valor apuntado en memoria."""
        postfix = ctx.postfix()
        ref_type = self.info.expr_type.get(postfix)
        self.visit(postfix)
        if isinstance(ref_type, RefT):
            target = ref_type.target
            self.emit("f64.load" if target == F64 else "i32.load")