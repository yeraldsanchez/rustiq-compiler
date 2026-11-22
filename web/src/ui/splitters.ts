/** Separadores para cambiar el ancho del editor y el reparto de alto entre
 *  la salida y los errores. Escriben variables CSS en `.app` (ver la grilla
 *  en styles.css) y recuerdan el reparto entre visitas. */

import { dom } from "../dom";
import { KEYS, load, save } from "../storage";

interface Layout {
  /** Fracción del ancho para el editor. */
  editor: number;
  /** Fracción del alto (salida + errores) para la salida. */
  output: number;
}

const DEFAULT_LAYOUT: Layout = { editor: 0.58, output: 0.6 };
const EDITOR_RANGE = [0.3, 0.78] as const;
const OUTPUT_RANGE = [0.2, 0.85] as const;

const app = document.querySelector<HTMLElement>(".app")!;
const outputTile = document.querySelector<HTMLElement>(".output")!;
const errorsTile = document.querySelector<HTMLElement>(".errors")!;

let layout = loadLayout();

function clamp(value: number, [min, max]: readonly [number, number]): number {
  return Math.min(Math.max(value, min), max);
}

function loadLayout(): Layout {
  try {
    const saved = JSON.parse(load(KEYS.layout) ?? "null") as Partial<Layout> | null;
    return {
      editor: clamp(Number(saved?.editor) || DEFAULT_LAYOUT.editor, EDITOR_RANGE),
      output: clamp(Number(saved?.output) || DEFAULT_LAYOUT.output, OUTPUT_RANGE),
    };
  } catch {
    return { ...DEFAULT_LAYOUT };
  }
}

function apply(): void {
  app.style.setProperty("--editor-width", `${(layout.editor * 100).toFixed(2)}%`);
  app.style.setProperty("--output-fr", `${layout.output.toFixed(3)}fr`);
  app.style.setProperty("--errors-fr", `${(1 - layout.output).toFixed(3)}fr`);
}

/** Arrastre con el puntero: `update` recibe el evento y ajusta `layout`. */
function makeDraggable(handle: HTMLElement, update: (event: PointerEvent) => void, reset: () => void): void {
  // Propio y no `hasPointerCapture`: en `pointerup` el navegador ya soltó la
  // captura y el arrastre no terminaría nunca.
  let dragging = false;
  const axisClass = handle === dom.splitX ? "resize-x" : "resize-y";

  handle.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    dragging = true;
    handle.setPointerCapture(event.pointerId);
    handle.classList.add("is-dragging");
    document.body.classList.add("is-resizing", axisClass);
  });
  handle.addEventListener("pointermove", (event) => {
    if (!dragging) return;
    update(event);
    apply();
  });
  const stop = () => {
    if (!dragging) return;
    dragging = false;
    handle.classList.remove("is-dragging");
    document.body.classList.remove("is-resizing", axisClass);
    save(KEYS.layout, JSON.stringify(layout));
  };
  handle.addEventListener("pointerup", stop);
  handle.addEventListener("pointercancel", stop);
  handle.addEventListener("lostpointercapture", stop);
  handle.addEventListener("dblclick", () => {
    reset();
    apply();
    save(KEYS.layout, JSON.stringify(layout));
  });
}

export function initSplitters(): void {
  apply();

  makeDraggable(
    dom.splitX,
    (event) => {
      const box = app.getBoundingClientRect();
      const padding = parseFloat(getComputedStyle(app).paddingLeft);
      const width = box.width - padding * 2;
      layout.editor = clamp((event.clientX - box.left - padding) / width, EDITOR_RANGE);
    },
    () => (layout.editor = DEFAULT_LAYOUT.editor),
  );

  makeDraggable(
    dom.splitY,
    (event) => {
      const top = outputTile.getBoundingClientRect().top;
      const bottom = errorsTile.getBoundingClientRect().bottom;
      layout.output = clamp((event.clientY - top) / (bottom - top), OUTPUT_RANGE);
    },
    () => (layout.output = DEFAULT_LAYOUT.output),
  );
}
