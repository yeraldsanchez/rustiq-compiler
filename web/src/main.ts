/** Punto de entrada: conecta el editor, el compilador remoto, la ejecución
 *  y los paneles. Cada pieza vive en su módulo; aquí solo se coordinan. */

import { CompileCancelledError, compileSource, ConnectionError, decodeBase64, ServerBusyError } from "./api";
import { dom } from "./dom";
import { createEditor } from "./editor/editor";
import type { Reference } from "./editor/navigation";
import { EXAMPLE_GROUPS, findExample, type Example } from "./examples";
import {
  activeFile,
  addFile,
  allFiles,
  EXTENSION,
  findByName,
  initFiles,
  onFilesChange,
  recentlyClosed,
  removeFile,
  reopenFile,
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
import { exampleGroups, fileGroups, outlineGroups, shortcutGroups } from "./ui/panelContent";
import { openPicker, togglePicker } from "./ui/picker";
import { initSidePanel, openPanel, refreshPanel, togglePanel } from "./ui/sidePanel";
import { initSplitters } from "./ui/splitters";
import { errorCountLabel, setCompileTime, setModuleSize, setState } from "./ui/status";
import { showToast } from "./ui/toast";
import { initWelcome, showWelcome } from "./ui/welcome";

const DEFAULT_EXAMPLE = "hola_mundo.rq";
const EMPTY_PROGRAM = "fn main() {\n}\n";
// Igual al límite del servidor (MAX_SOURCE_CHARS en server/app.py).
const MAX_OPEN_BYTES = 20_000;
const OUTLINE_REFRESH_MS = 250;

const runner = new Runner();
// Compilaciones visibles en curso (las de Compilar y Ejecutar). Las de los
// errores en vivo no bloquean los botones.
let visibleCompiles = 0;
// Cada compilación se numera; solo se pinta la respuesta de la más reciente,
// por si llegan desordenadas.
let latestRequest = 0;
let live: LiveErrors | null = null;
let outlineTimer: number | undefined;
// Los errores de la última compilación de cada archivo, para volver a
// mostrarlos al cambiar de pestaña.
const errorsByFile = new Map<string, CompileError[]>();

initFiles(() => ({ name: DEFAULT_EXAMPLE, source: findExample(DEFAULT_EXAMPLE)?.source ?? EMPTY_PROGRAM }));

const editor = createEditor(dom.editor, {
  onChange(source) {
    const file = activeFile();
    if (file) updateSource(file.id, source);
    live?.notifyChange();
    // El esquema sigue al texto mientras su panel está abierto.
    window.clearTimeout(outlineTimer);
    outlineTimer = window.setTimeout(() => refreshPanel("outline"), OUTLINE_REFRESH_MS);
  },
  onCursor(line, column) {
    dom.cursorPos.textContent = `Ln ${line}, Col ${column}`;
  },
  onCompile: () => void compile(),
  onRun: () => void compileAndRun(),
  onOutline: () => openPanel("outline", true),
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
  // Sin archivos abiertos no hay nada que compilar.
  const idle = busy || activeFile() === null;
  dom.compileButton.disabled = idle;
  dom.runButton.disabled = idle;
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
  if (!file) return null;
  if (!quiet) {
    visibleCompiles += 1;
    updateButtons();
    setState("Compilando…", "neutral");
  }
  const started = performance.now();

  try {
    const result = await compileSource(editor.getSource());
    if (request !== latestRequest || activeFile()?.id !== file.id) return null;
    hideBanner();
    showCompileResult(result, performance.now() - started, file.id, file.name);
    return result;
  } catch (error) {
    if (error instanceof CompileCancelledError) return null;
    if (!(error instanceof ConnectionError)) throw error;
    if (request !== latestRequest) return null;
    if (error instanceof ServerBusyError) {
      // En vivo no se muestra nada: la siguiente edición vuelve a intentar.
      if (quiet) return null;
      showBanner(error.message, () => void compile());
      setState("Servidor ocupado", "warn");
      return null;
    }
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

/** Muestra el archivo activo con sus últimos errores, o el inicio si no
 *  queda ninguno abierto. */
function showActiveFile(): void {
  const file = activeFile();
  renderFileTabs();
  showWelcome(file === null, recentlyClosed());
  refreshPanel();
  updateButtons();
  if (!file) {
    // Sin archivos, los indicadores de la última compilación ya no aplican.
    renderErrors([], errorHandlers);
    setCompileTime(null);
    setModuleSize(null);
    if (!runner.running) setState("Listo", "empty");
    return;
  }
  editor.open(file.id, file.source);
  renderErrors(errorsByFile.get(file.id) ?? [], errorHandlers);
  live?.notifyChange();
}

function createFile(name = `nuevo${EXTENSION}`, source = EMPTY_PROGRAM): void {
  addFile(name, source);
  editor.focus();
}

function closeFile(id: string): void {
  const file = removeFile(id);
  if (!file) return;
  editor.forget(id);
  errorsByFile.delete(id);
  showToast(`Se cerró ${file.name}.`, { label: "Deshacer", run: () => reopen(id) });
}

function reopen(id: string): void {
  if (reopenFile(id)) editor.focus();
}

function openExample(example: Example): void {
  const existing = findByName(example.name);
  if (existing && existing.source === example.source) setActive(existing.id);
  else addFile(example.name, example.source);
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
  if (file) download(editor.getSource(), file.name, "text/plain");
}

onFilesChange(showActiveFile);

// --- Panel lateral, referencias y atajos -----------------------------------

initSidePanel(
  {
    files: {
      groups: () =>
        fileGroups(allFiles(), activeFile(), {
          select: setActive,
          close: closeFile,
          download: downloadActive,
          rename: renameActiveTab,
        }),
      empty: () => "Ningún archivo abierto.",
    },
    outline: {
      groups: () => (activeFile() ? outlineGroups(editor.outline(), (item) => editor.select(item)) : []),
      empty: () => (activeFile() ? "Este archivo todavía no declara nada." : "Abre un archivo para ver su esquema."),
    },
    examples: {
      groups: () => exampleGroups(EXAMPLE_GROUPS, activeFile()?.name ?? null, openExample),
      empty: () => "Ningún ejemplo coincide.",
    },
  },
  () => editor.focus(),
);

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

function showShortcuts(): void {
  openPicker({ anchor: dom.railKeys, side: "right", label: "Atajos de teclado", width: 340, groups: shortcutGroups() });
}

// --- Botones y atajos ------------------------------------------------------

dom.railKeys.addEventListener("click", () => togglePicker(dom.railKeys, showShortcuts));
dom.sideNewButton.addEventListener("click", () => createFile());
dom.sideOpenButton.addEventListener("click", openFromDisk);
dom.compileButton.addEventListener("click", () => void compile());
dom.runButton.addEventListener("click", () => void compileAndRun());
dom.stopButton.addEventListener("click", () => runner.stop());

// Los atajos también funcionan con el foco fuera del editor.
document.addEventListener("keydown", (event) => {
  if (event.defaultPrevented) return;
  const mod = event.ctrlKey || event.metaKey;
  const key = event.key.toLowerCase();
  let handled = true;
  if (mod && !event.shiftKey && key === "enter") void compileAndRun();
  else if (mod && !event.shiftKey && key === "b") void compile();
  else if (mod && !event.shiftKey && key === "o") openFromDisk();
  else if (mod && event.shiftKey && key === "e") togglePanel("files");
  else if (mod && event.shiftKey && key === "o") openPanel("outline", true);
  // Ctrl+N lo reserva el navegador para una ventana nueva.
  else if (event.altKey && !mod && key === "n") createFile();
  else handled = false;
  if (handled) event.preventDefault();
});

initWelcome({
  create: () => createFile(),
  openFromDisk,
  openExamples: () => openPanel("examples", true),
  reopen,
});
initFileTabs({ select: setActive, close: closeFile, create: () => createFile() });
showActiveFile();
initSplitters();
live = initLiveErrors(() => void compile({ quiet: true }));
updateButtons();
