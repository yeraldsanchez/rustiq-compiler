/** Lista flotante junto a un punto de la pantalla: las referencias de un
 *  símbolo y los atajos de teclado. Se cierra con Esc, al elegir algo o al
 *  hacer clic fuera. Solo hay una abierta. */

import { createListView, type ListGroup } from "./listView";

export interface PickerOptions {
  /** Elemento o rectángulo junto al cual se abre. */
  anchor: HTMLElement | DOMRect;
  /** Para lectores de pantalla. */
  label: string;
  groups: ListGroup[];
  search?: boolean;
  placeholder?: string;
  empty?: string;
  width?: number;
  code?: boolean;
  /** "below" (por defecto) o "right": a la derecha del ancla, como un menú
   *  que sale del riel lateral. */
  side?: "below" | "right";
}

const MARGIN = 8;
const OFFSET = 6;
const DEFAULT_WIDTH = 380;

let close: ((restoreFocus: boolean) => void) | null = null;
// El botón que la abrió y cuándo se cerró por un clic en él: así ese mismo
// clic no la vuelve a abrir.
let lastClosed: { anchor: HTMLElement; at: number } | null = null;
const REOPEN_GUARD_MS = 400;

/** Para el clic de un botón que abre una lista: la abre o, si la acaba de
 *  cerrar ese mismo clic, no hace nada. */
export function togglePicker(anchor: HTMLElement, show: () => void): void {
  const guard = lastClosed;
  lastClosed = null;
  if (guard && guard.anchor === anchor && performance.now() - guard.at < REOPEN_GUARD_MS) return;
  show();
}

function place(root: HTMLElement, anchor: HTMLElement | DOMRect, side: "below" | "right"): void {
  const rect = anchor instanceof HTMLElement ? anchor.getBoundingClientRect() : anchor;
  const { innerWidth, innerHeight } = window;
  const width = root.offsetWidth;
  const height = root.offsetHeight;
  let left: number;
  let top: number;
  if (side === "right") {
    left = rect.right + OFFSET;
    top = Math.min(rect.top, innerHeight - height - MARGIN);
  } else {
    left = rect.left;
    const below = rect.bottom + OFFSET;
    top = below + height <= innerHeight - MARGIN ? below : rect.top - OFFSET - height;
  }
  left = Math.min(left, innerWidth - width - MARGIN);
  root.style.left = `${Math.max(MARGIN, left)}px`;
  root.style.top = `${Math.max(MARGIN, top)}px`;
}

export function openPicker(options: PickerOptions): void {
  close?.(false);
  const previousFocus = document.activeElement as HTMLElement | null;
  const anchorElement = options.anchor instanceof HTMLElement ? options.anchor : null;

  const view = createListView({
    label: options.label,
    search: options.search,
    placeholder: options.placeholder,
    empty: options.empty,
    code: options.code,
    onChoose: () => finish(false),
    onEscape: () => finish(true),
  });

  const root = document.createElement("div");
  root.className = "picker";
  root.setAttribute("role", "dialog");
  root.setAttribute("aria-label", options.label);
  root.style.width = `${Math.min(options.width ?? DEFAULT_WIDTH, window.innerWidth - 2 * MARGIN)}px`;
  root.append(view.root);

  function onPointerDown(event: PointerEvent): void {
    const target = event.target as Node;
    if (root.contains(target)) return;
    if (anchorElement?.contains(target)) lastClosed = { anchor: anchorElement, at: performance.now() };
    finish(false);
  }

  function onKeyDown(event: KeyboardEvent): void {
    if (event.key === "Tab") finish(false);
  }

  const onResize = () => finish(false);

  function finish(restoreFocus: boolean): void {
    if (close !== finish) return;
    close = null;
    root.remove();
    document.removeEventListener("pointerdown", onPointerDown, true);
    window.removeEventListener("resize", onResize);
    anchorElement?.setAttribute("aria-expanded", "false");
    if (restoreFocus) previousFocus?.focus();
  }

  root.addEventListener("keydown", onKeyDown);
  document.addEventListener("pointerdown", onPointerDown, true);
  window.addEventListener("resize", onResize);

  document.body.append(root);
  close = finish;
  view.setGroups(options.groups);
  place(root, options.anchor, options.side ?? "below");
  anchorElement?.setAttribute("aria-expanded", "true");
  view.focus();
}
