/** Lista flotante con búsqueda: la usan el selector de ejemplos, el esquema,
 *  las referencias y el menú de archivo. Se maneja con el teclado (flechas,
 *  Enter, Esc) y se cierra al hacer clic fuera. Solo hay una abierta. */

export interface PickerItem {
  title: string;
  detail?: string;
  /** Texto corto a la derecha: posición, código de error, atajo. */
  meta?: string;
  metaTone?: "error" | "accent";
  /** Texto extra para la búsqueda que no se muestra. */
  keywords?: string;
  /** Marca el elemento actual (por ejemplo, el archivo abierto). */
  current?: boolean;
  onSelect(): void;
}

export interface PickerGroup {
  label?: string;
  items: PickerItem[];
}

export interface PickerOptions {
  /** Elemento o rectángulo debajo del cual se abre. */
  anchor: HTMLElement | DOMRect;
  /** Para lectores de pantalla. */
  label: string;
  groups: PickerGroup[];
  search?: boolean;
  placeholder?: string;
  empty?: string;
  width?: number;
  /** Los títulos son código (nombres, líneas del programa): van en mono. */
  code?: boolean;
}

const MARGIN = 8;
const OFFSET = 6;
const DEFAULT_WIDTH = 380;

interface Open {
  root: HTMLElement;
  close(restoreFocus: boolean): void;
}

let open: Open | null = null;
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

export function closePicker(): void {
  open?.close(true);
}

export function isPickerOpen(): boolean {
  return open !== null;
}

/** Quita tildes y mayúsculas para buscar "funcion" y encontrar "función". */
function normalize(text: string): string {
  return text.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function searchText(item: PickerItem): string {
  return normalize([item.title, item.detail, item.meta, item.keywords].filter(Boolean).join(" "));
}

function place(root: HTMLElement, anchor: HTMLElement | DOMRect): void {
  const rect = anchor instanceof HTMLElement ? anchor.getBoundingClientRect() : anchor;
  const { innerWidth, innerHeight } = window;
  const width = root.offsetWidth;
  const height = root.offsetHeight;
  const left = Math.min(Math.max(MARGIN, rect.left), innerWidth - width - MARGIN);
  const below = rect.bottom + OFFSET;
  const fitsBelow = below + height <= innerHeight - MARGIN;
  const top = fitsBelow ? below : Math.max(MARGIN, rect.top - OFFSET - height);
  root.style.left = `${Math.max(MARGIN, left)}px`;
  root.style.top = `${top}px`;
}

export function openPicker(options: PickerOptions): void {
  open?.close(false);
  const previousFocus = document.activeElement as HTMLElement | null;

  const root = document.createElement("div");
  root.className = options.code ? "picker picker-code" : "picker";
  root.setAttribute("role", "dialog");
  root.setAttribute("aria-label", options.label);
  root.style.width = `${Math.min(options.width ?? DEFAULT_WIDTH, window.innerWidth - 2 * MARGIN)}px`;

  const input = document.createElement("input");
  input.className = "picker-search";
  input.type = "text";
  input.spellcheck = false;
  input.autocomplete = "off";
  input.placeholder = options.placeholder ?? "Buscar…";
  input.setAttribute("aria-label", options.placeholder ?? "Buscar");

  const list = document.createElement("ul");
  list.className = "picker-list";
  list.setAttribute("role", "listbox");
  list.tabIndex = -1;

  const emptyNote = document.createElement("p");
  emptyNote.className = "picker-empty";
  emptyNote.textContent = options.empty ?? "Nada coincide.";

  if (options.search) root.append(input);
  root.append(list, emptyNote);

  // Elementos visibles en orden, para moverse con las flechas.
  let visible: { item: PickerItem; element: HTMLLIElement }[] = [];
  let active = 0;

  function setActive(index: number, scroll = true): void {
    if (!visible.length) return;
    visible[active]?.element.setAttribute("aria-selected", "false");
    active = (index + visible.length) % visible.length;
    const { element } = visible[active];
    element.setAttribute("aria-selected", "true");
    list.setAttribute("aria-activedescendant", element.id);
    input.setAttribute("aria-activedescendant", element.id);
    if (scroll) element.scrollIntoView({ block: "nearest" });
  }

  function choose(item: PickerItem): void {
    close(false);
    item.onSelect();
  }

  function render(): void {
    const query = normalize(input.value.trim());
    const nodes: HTMLLIElement[] = [];
    visible = [];
    let counter = 0;
    for (const group of options.groups) {
      const matches = group.items.filter((item) => !query || searchText(item).includes(query));
      if (!matches.length) continue;
      if (group.label) {
        const label = document.createElement("li");
        label.className = "picker-group";
        label.setAttribute("role", "presentation");
        label.textContent = group.label;
        nodes.push(label);
      }
      for (const item of matches) {
        const element = itemElement(item, `picker-item-${counter++}`);
        const index = visible.length;
        element.addEventListener("mousemove", () => active !== index && setActive(index, false));
        element.addEventListener("click", () => choose(item));
        visible.push({ item, element });
        nodes.push(element);
      }
    }
    list.replaceChildren(...nodes);
    emptyNote.hidden = visible.length > 0;
    const current = visible.findIndex(({ item }) => item.current);
    active = 0;
    setActive(query || current < 0 ? 0 : current);
  }

  function onKeyDown(event: KeyboardEvent): void {
    switch (event.key) {
      case "ArrowDown":
        setActive(active + 1);
        break;
      case "ArrowUp":
        setActive(active - 1);
        break;
      case "Home":
        if (options.search) return;
        setActive(0);
        break;
      case "End":
        if (options.search) return;
        setActive(visible.length - 1);
        break;
      case "Enter":
        if (visible[active]) choose(visible[active].item);
        break;
      case "Escape":
        close(true);
        break;
      case "Tab":
        close(false);
        return;
      default:
        return;
    }
    event.preventDefault();
    event.stopPropagation();
  }

  function onPointerDown(event: PointerEvent): void {
    const target = event.target as Node;
    if (root.contains(target)) return;
    if (options.anchor instanceof HTMLElement && options.anchor.contains(target)) {
      lastClosed = { anchor: options.anchor, at: performance.now() };
    }
    close(false);
  }

  function onResize(): void {
    close(false);
  }

  function close(restoreFocus: boolean): void {
    if (open?.root !== root) return;
    open = null;
    root.remove();
    document.removeEventListener("pointerdown", onPointerDown, true);
    window.removeEventListener("resize", onResize);
    options.anchor instanceof HTMLElement && options.anchor.setAttribute("aria-expanded", "false");
    if (restoreFocus) previousFocus?.focus();
  }

  input.addEventListener("input", render);
  root.addEventListener("keydown", onKeyDown);
  document.addEventListener("pointerdown", onPointerDown, true);
  window.addEventListener("resize", onResize);

  document.body.append(root);
  open = { root, close };
  render();
  place(root, options.anchor);
  if (options.anchor instanceof HTMLElement) options.anchor.setAttribute("aria-expanded", "true");
  (options.search ? input : list).focus();
}

function itemElement(item: PickerItem, id: string): HTMLLIElement {
  const element = document.createElement("li");
  element.className = "picker-item";
  element.id = id;
  element.setAttribute("role", "option");
  element.setAttribute("aria-selected", "false");
  if (item.current) element.classList.add("is-current");

  const title = document.createElement("span");
  title.className = "picker-title";
  title.textContent = item.title;
  element.append(title);

  if (item.meta) {
    const meta = document.createElement("span");
    meta.className = "picker-meta";
    if (item.metaTone) meta.classList.add(`is-${item.metaTone}`);
    meta.textContent = item.meta;
    element.append(meta);
  }
  if (item.detail) {
    const detail = document.createElement("span");
    detail.className = "picker-detail";
    detail.textContent = item.detail;
    element.append(detail);
  }
  return element;
}
