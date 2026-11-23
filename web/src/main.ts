/** Punto de entrada: conecta el editor, el compilador remoto, la ejecución
 *  y los paneles. Cada pieza vive en su módulo; aquí solo se coordinan. */

import { compileSource, ConnectionError, decodeBase64 } from "./api";
import { dom } from "./dom";
import { createEditor } from "./editor/editor";
import type { Reference } from "./editor/navigation";
import type { OutlineKind } from "./editor/outline";
import { EXAMPLE_GROUPS, findExample, type Example } from "./examples";
import {
  activeFile,
  addFile,
  allFiles,
  EXTENSION,
  findByName,
  findFile,
  initFiles,
  onFilesChange,
  removeFile,
  setActive,
  updateSource,
} from "./files";
import { Runner, TIME_LIMIT_MS, type RunResult } from "./run/runner";
import type { CompileError, CompileResponse } from "./types";
import { hideBanner, showBanner } from "./ui/banner";
import { renderErrors, type ErrorListHandlers } from "./ui/errors";
import { initFileTabs, renameActiveTab, renderFileTabs } from "./ui/fileTabs";
import { openInlinePrompt } from "./ui/inlinePrompt";
import { initLiveErrors, type LiveErrors } from "./ui/liveToggle";
import { appendNote, clearOutput, download, printLine, selectTab, setModule, showOutputMessage } from "./ui/output";
import { openPicker, togglePicker, type PickerGroup } from "./ui/picker";
import { initSplitters } from "./ui/splitters";
import { errorCountLabel, setCompileTime, setModuleSize, setState } from "./ui/status";
import { showToast } from "./ui/toast";

const DEFAULT_EXAMPLE = "hola_mundo.rq";
const EMPTY_PROGRAM = "fn main() {\n}\n";
const MAX_OPEN_BYTES = 100_000;

const runner = new Runner();
// Compilaciones visibles en curso (las de Compilar y Ejecutar). Las de los
// errores en vivo no bloquean los botones.
let visibleCompiles = 0;
// Cada compilación se numera; solo se pinta la respuesta de la más reciente,
// por si llegan desordenadas.
let latestRequest = 0;
let live: LiveErrors | null = null;
// Los errores de la última compilación de cada archivo, para volver a
// mostrarlos al cambiar de pestaña.
const errorsByFile = new Map<string, CompileError[]>();

initFiles(() => ({ name: DEFAULT_EXAMPLE, source: findExample(DEFAULT_EXAMPLE)?.source ?? EMPTY_PROGRAM }));

const editor = createEditor(dom.editor, {
  onChange(source) {
    updateSource(activeFile().id, source);
    live?.notifyChange();
  },
  onCursor(line, column) {
    dom.cursorPos.textContent = `Ln ${line}, Col ${column}`;
  },
  onCompile: () => void compile(),
  onRun: () => void compileAndRun(),
  onOutline: () => showOutline(),
  async refreshSymbols() {
    await compile({ quiet: true });
  },
  showReferences,
  promptRename(name, anchor, submit) {
    openInlinePrompt({ anchor, title: `Renombrar '${name}'`, value: name, submit });
  },
  notify: (message) => showToast(message),
});

const errorHandlers: ErrorListHandlers = {
  select: (error) => editor.goTo(error.line, error.column),
  fixes: (error) => editor.fixesFor(error),
  applyFix: (error, fix) => editor.applyFix(error, fix),
};

function updateButtons(): void {
  const busy = visibleCompiles > 0 || runner.running;
  dom.compileButton.disabled = busy;
  dom.runButton.disabled = busy;
  dom.stopButton.disabled = !runner.running;
}

/** Compila y pinta el resultado. Devuelve null si no hubo respuesta o si
 *  otra compilación más reciente la dejó obsoleta. `quiet` es para los
 *  errores en vivo: no muestra "Compilando…" ni bloquea los botones. */
async function compile({ quiet = false } = {}): Promise<CompileResponse | null> {
  if (runner.running || (!quiet && visibleCompiles > 0)) return null;
  const request = ++latestRequest;
  // Si se cambia de pestaña mientras compila, la respuesta ya no aplica.
  const file = activeFile();
  if (!quiet) {
    visibleCompiles += 1;
    updateButtons();
    setState("Compilando…", "neutral");
  }
  const started = performance.now();

  try {
    const result = await compileSource(editor.getSource());
    if (request !== latestRequest || activeFile().id !== file.id) return null;
    hideBanner();
    showCompileResult(result, performance.now() - started, file.id, file.name);
    return result;
  } catch (error) {
    if (!(error instanceof ConnectionError)) throw error;
    if (request !== latestRequest) return null;
    showBanner(error.message, () => void compile());
    setState("Sin conexión", "error");
    return null;
  } finally {
    if (!quiet) visibleCompiles -= 1;
    updateButtons();
  }
}

function showCompileResult(result: CompileResponse, elapsedMs: number, fileId: string, fileName: string): void {
  const wasm = result.wasm_base64 ? decodeBase64(result.wasm_base64) : null;
  setCompileTime(elapsedMs);
  setModuleSize(wasm ? wasm.byteLength : null);
  setModule(result.wat, wasm, fileName);
  // Primero los símbolos: los arreglos rápidos de los errores los usan.
  editor.showSymbols(result.symbols ?? []);
  editor.showErrors(result.errors);
  errorsByFile.set(fileId, result.errors);
  renderErrors(result.errors, errorHandlers);
  if (result.ok) setState("Compilado", "ok");
  else setState(errorCountLabel(result.errors.length), "error");
}

async function compileAndRun(): Promise<void> {
  const result = await compile();
  if (!result) return;
  if (!result.ok || !result.wasm_base64) {
    showOutputMessage("No hay nada que ejecutar. Corrige los errores de compilación y vuelve a intentarlo.");
    return;
  }

  selectTab("output");
  clearOutput();
  setState("Ejecutando…", "neutral");
  runner.run(decodeBase64(result.wasm_base64), {
    onPrint: printLine,
    onFinish: showRunResult,
  });
  updateButtons();
}

function showRunResult(result: RunResult): void {
  switch (result.status) {
    case "ok":
      setState("Terminado", "ok");
      appendNote(`Programa terminado en ${Math.round(result.elapsedMs)} ms.`, "note");
      break;
    case "trap":
      setState("Error en ejecución", "warn");
      appendNote(`Error en ejecución: ${result.message}.`, "trap");
      break;
    case "error":
      setState("Error en ejecución", "warn");
      appendNote(`No se pudo ejecutar: ${result.message}`, "trap");
      break;
    case "limit":
      setState("Detenido", "warn");
      appendNote("Ejecución detenida: el programa imprimió demasiadas líneas.", "trap");
      break;
    case "timeout":
      setState("Tiempo agotado", "warn");
      appendNote(`Ejecución detenida: pasó el límite de ${TIME_LIMIT_MS / 1000} s. ¿Hay un ciclo infinito?`, "trap");
      break;
    case "stopped":
      setState("Detenido", "warn");
      appendNote("Ejecución detenida.", "note");
      break;
  }
  updateButtons();
}

// --- Archivos --------------------------------------------------------------

/** Muestra en el editor el archivo activo, con sus últimos errores. */
function showActiveFile(): void {
  // Al cerrar el último archivo hay un instante sin ninguno; closeFile crea
  // uno nuevo enseguida.
  if (!allFiles().length) return;
  const file = activeFile();
  editor.open(file.id, file.source);
  renderErrors(errorsByFile.get(file.id) ?? [], errorHandlers);
  renderFileTabs();
  live?.notifyChange();
}

function createFile(name = `nuevo${EXTENSION}`, source = EMPTY_PROGRAM): void {
  addFile(name, source);
  editor.focus();
}

function closeFile(id: string): void {
  const removed = removeFile(id);
  if (!removed) return;
  const { file, index } = removed;
  editor.forget(id);
  errorsByFile.delete(id);
  // Nunca queda el editor sin archivos.
  if (!allFiles().length) addFile(`main${EXTENSION}`, EMPTY_PROGRAM);
  showToast(`Se cerró ${file.name}.`, {
    label: "Deshacer",
    run: () => {
      // Si solo quedó el archivo vacío que se creó al cerrar, se reemplaza.
      const [only] = allFiles();
      const placeholder = allFiles().length === 1 && only.source === EMPTY_PROGRAM ? only.id : null;
      addFile(file.name, file.source, index, file.id);
      if (placeholder) {
        removeFile(placeholder);
        editor.forget(placeholder);
      }
    },
  });
}

function openExample(example: Example): void {
  const existing = findByName(example.name);
  if (existing && existing.source === example.source) setActive(existing.id);
  else addFile(example.name, example.source);
  editor.focus();
}

function openFromDisk(): void {
  dom.fileInput.value = "";
  dom.fileInput.click();
}

dom.fileInput.addEventListener("change", async () => {
  const picked = dom.fileInput.files?.[0];
  if (!picked) return;
  if (picked.size > MAX_OPEN_BYTES) {
    showToast(`${picked.name} es demasiado grande para el editor.`);
    return;
  }
  const name = picked.name.replace(/\.(rs|txt)$/, EXTENSION);
  addFile(name, await picked.text());
  editor.focus();
});

function downloadActive(): void {
  const file = activeFile();
  download(editor.getSource(), file.name, "text/plain");
}

function showFileMenu(): void {
  const file = activeFile();
  openPicker({
    anchor: dom.fileMenuButton,
    label: "Archivo",
    width: 260,
    groups: [
      {
        items: [
          { title: "Archivo nuevo", meta: "+", onSelect: () => createFile() },
          { title: "Abrir desde el disco…", meta: ".rq", onSelect: openFromDisk },
          { title: `Descargar ${file.name}`, onSelect: downloadActive },
        ],
      },
      {
        items: [
          { title: "Renombrar", meta: "F2 en la pestaña", onSelect: renameActiveTab },
          { title: `Cerrar ${file.name}`, onSelect: () => closeFile(file.id) },
        ],
      },
    ],
  });
}

onFilesChange(showActiveFile);

// --- Ejemplos --------------------------------------------------------------

function showExamples(): void {
  const groups: PickerGroup[] = EXAMPLE_GROUPS.filter((g) => g.examples.length).map((group) => ({
    label: group.label,
    items: group.examples.map((example) => ({
      title: example.title,
      detail: example.description || undefined,
      meta: example.errorCode,
      metaTone: example.errorCode ? "error" : undefined,
      keywords: example.name,
      current: findFile(activeFile().id)?.name === example.name,
      onSelect: () => openExample(example),
    })),
  }));
  openPicker({
    anchor: dom.examples,
    label: "Ejemplos",
    groups,
    search: true,
    width: 440,
    placeholder: "Buscar un ejemplo o un código de error…",
    empty: "Ningún ejemplo coincide.",
  });
}

// --- Esquema y referencias -------------------------------------------------

const OUTLINE_GROUPS: [OutlineKind, string][] = [
  ["func", "Funciones"],
  ["struct", "Structs"],
  ["enum", "Enums"],
  ["const", "Constantes"],
];

function showOutline(): void {
  const items = editor.outline();
  openPicker({
    anchor: dom.outlineButton,
    label: "Esquema del programa",
    search: true,
    code: true,
    width: 420,
    placeholder: "Ir a una función, struct, enum o constante…",
    empty: items.length ? "Nada coincide." : "Este archivo todavía no declara nada.",
    groups: OUTLINE_GROUPS.map(([kind, label]) => ({
      label,
      items: items
        .filter((item) => item.kind === kind)
        .map((item) => ({
          title: item.name,
          detail: item.detail,
          meta: `${item.line}`,
          onSelect: () => editor.select(item),
        })),
    })),
  });
}

function showReferences(name: string, references: Reference[], anchor: DOMRect): void {
  const count = references.length === 1 ? "1 aparición" : `${references.length} apariciones`;
  openPicker({
    anchor,
    label: `Referencias de ${name}`,
    width: 420,
    code: true,
    groups: [
      {
        label: `Referencias · ${count}`,
        items: references.map((ref) => ({
          title: ref.preview,
          detail: ref.declaration ? "declaración" : undefined,
          meta: `${ref.line}:${ref.column}`,
          metaTone: ref.declaration ? "accent" : undefined,
          onSelect: () => editor.select(ref),
        })),
      },
    ],
  });
}

// --- Botones y atajos ------------------------------------------------------

dom.examples.addEventListener("click", () => togglePicker(dom.examples, showExamples));
dom.outlineButton.addEventListener("click", () => togglePicker(dom.outlineButton, showOutline));
dom.fileMenuButton.addEventListener("click", () => togglePicker(dom.fileMenuButton, showFileMenu));
dom.compileButton.addEventListener("click", () => void compile());
dom.runButton.addEventListener("click", () => void compileAndRun());
dom.stopButton.addEventListener("click", () => runner.stop());

// Los atajos también funcionan con el foco fuera del editor.
document.addEventListener("keydown", (event) => {
  if (!(event.ctrlKey || event.metaKey) || event.defaultPrevented) return;
  if (event.key === "Enter") {
    event.preventDefault();
    void compileAndRun();
  } else if (event.key.toLowerCase() === "b") {
    event.preventDefault();
    void compile();
  }
});

initFileTabs({ select: setActive, close: closeFile, create: () => createFile() });
showActiveFile();
initSplitters();
live = initLiveErrors(() => void compile({ quiet: true }));
updateButtons();
