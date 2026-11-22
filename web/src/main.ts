/** Punto de entrada: conecta el editor, el compilador remoto, la ejecución
 *  y los paneles. Cada pieza vive en su módulo; aquí solo se coordinan. */

import { compileSource, ConnectionError, decodeBase64 } from "./api";
import { dom } from "./dom";
import { createEditor } from "./editor/editor";
import { EXAMPLE_GROUPS, findExample } from "./examples";
import { Runner, TIME_LIMIT_MS, type RunResult } from "./run/runner";
import { loadSource, saveSource } from "./storage";
import type { CompileError, CompileResponse } from "./types";
import { hideBanner, showBanner } from "./ui/banner";
import { renderErrors } from "./ui/errors";
import { appendNote, clearOutput, printLine, selectTab, setModule, showOutputMessage } from "./ui/output";
import { errorCountLabel, setCompileTime, setModuleSize, setState } from "./ui/status";

const DEFAULT_EXAMPLE = "test_b4_strings.rq";
const SAVE_DELAY_MS = 300;

const runner = new Runner();
let compiling = false;
let saveTimer: number | undefined;

const editor = createEditor(dom.editor, initialSource(), {
  onChange(source) {
    window.clearTimeout(saveTimer);
    saveTimer = window.setTimeout(() => saveSource(source), SAVE_DELAY_MS);
  },
  onCursor(line, column) {
    dom.cursorPos.textContent = `Ln ${line}, Col ${column}`;
  },
  onCompile: () => void compile(),
  onRun: () => void compileAndRun(),
});

function initialSource(): string {
  return loadSource() ?? findExample(DEFAULT_EXAMPLE)?.source ?? "fn main() {\n}\n";
}

function updateButtons(): void {
  const busy = compiling || runner.running;
  dom.compileButton.disabled = busy;
  dom.runButton.disabled = busy;
  dom.stopButton.disabled = !runner.running;
}

function goToError(error: CompileError): void {
  editor.goTo(error.line, error.column);
}

/** Compila y pinta el resultado. Devuelve null si no hubo respuesta. */
async function compile(): Promise<CompileResponse | null> {
  if (compiling || runner.running) return null;
  compiling = true;
  updateButtons();
  setState("Compilando…", "neutral");
  const started = performance.now();

  try {
    const result = await compileSource(editor.getSource());
    hideBanner();
    showCompileResult(result, performance.now() - started);
    return result;
  } catch (error) {
    if (!(error instanceof ConnectionError)) throw error;
    showBanner(error.message, () => void compile());
    setState("Sin conexión", "error");
    return null;
  } finally {
    compiling = false;
    updateButtons();
  }
}

function showCompileResult(result: CompileResponse, elapsedMs: number): void {
  const wasm = result.wasm_base64 ? decodeBase64(result.wasm_base64) : null;
  setCompileTime(elapsedMs);
  setModuleSize(wasm ? wasm.byteLength : null);
  setModule(result.wat, wasm);
  renderErrors(result.errors, goToError);
  editor.showErrors(result.errors);
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

function fillExamples(): void {
  for (const group of EXAMPLE_GROUPS) {
    if (!group.examples.length) continue;
    const optgroup = document.createElement("optgroup");
    optgroup.label = group.label;
    for (const example of group.examples) optgroup.append(new Option(example.name, example.name));
    dom.examples.append(optgroup);
  }
}

dom.examples.addEventListener("change", () => {
  const example = findExample(dom.examples.value);
  if (!example) return;
  editor.setSource(example.source);
  editor.showErrors([]);
  renderErrors([], goToError);
});

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

fillExamples();
renderErrors([], goToError);
updateButtons();
