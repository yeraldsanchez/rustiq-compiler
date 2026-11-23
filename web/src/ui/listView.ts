/** Lista con búsqueda, grupos y teclado (flechas, Enter, Inicio, Fin). La
 *  usan las listas flotantes (ui/picker.ts) y las vistas del panel lateral
 *  (archivos, esquema y ejemplos). */

export interface ListAction {
  label: string;
  title: string;
  run(): void;
}

export interface ListItem {
  title: string;
  detail?: string;
  /** Texto corto a la derecha: posición, código de error, atajo. */
  meta?: string;
  metaTone?: "error" | "accent";
  /** Marca de una letra a la izquierda (ƒ, S, E, C) con su color. */
  badge?: { text: string; tone: "fn" | "type" | "enum" | "const" };
  /** Texto extra para la búsqueda que no se muestra. */
  keywords?: string;
  /** El elemento actual (el archivo abierto, el ejemplo activo). */
  current?: boolean;
  /** Botones pequeños a la derecha, como cerrar un archivo. */
  actions?: ListAction[];
  onSelect(): void;
}

export interface ListGroup {
  label?: string;
  items: ListItem[];
}

export interface ListViewOptions {
  /** Para lectores de pantalla. */
  label: string;
  search?: boolean;
  placeholder?: string;
  empty?: string;
  /** Los títulos son código (nombres, líneas del programa): van en mono. */
  code?: boolean;
  /** Se llama después de elegir un elemento con Enter o con clic. */
  onChoose?(): void;
  onEscape?(): void;
}

export interface ListView {
  root: HTMLElement;
  setGroups(groups: ListGroup[]): void;
  setEmptyText(text: string): void;
  /** Enfoca la búsqueda, o la lista si no hay búsqueda. */
  focus(): void;
}

let nextId = 0;

/** Quita tildes y mayúsculas para buscar "funcion" y encontrar "función". */
function normalize(text: string): string {
  return text.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function searchText(item: ListItem): string {
  return normalize([item.title, item.detail, item.meta, item.keywords].filter(Boolean).join(" "));
}

export function createListView(options: ListViewOptions): ListView {
  const prefix = `list-${nextId++}`;
  const root = document.createElement("div");
  root.className = options.code ? "list-view list-code" : "list-view";

  const input = document.createElement("input");
  input.className = "list-search";
  input.type = "text";
  input.spellcheck = false;
  input.autocomplete = "off";
  input.placeholder = options.placeholder ?? "Buscar…";
  input.setAttribute("aria-label", options.placeholder ?? "Buscar");

  const list = document.createElement("ul");
  list.className = "list-items";
  list.setAttribute("role", "listbox");
  list.setAttribute("aria-label", options.label);
  list.tabIndex = 0;

  const emptyNote = document.createElement("p");
  emptyNote.className = "list-empty";
  emptyNote.textContent = options.empty ?? "Nada coincide.";

  if (options.search) root.append(input);
  root.append(list, emptyNote);

  let groups: ListGroup[] = [];
  // Elementos visibles en orden, para moverse con las flechas.
  let visible: { item: ListItem; element: HTMLLIElement }[] = [];
  let active = -1;

  function setActive(index: number, scroll = true): void {
    if (!visible.length) return;
    if (visible[active]) visible[active].element.setAttribute("aria-selected", "false");
    active = (index + visible.length) % visible.length;
    const { element } = visible[active];
    element.setAttribute("aria-selected", "true");
    list.setAttribute("aria-activedescendant", element.id);
    input.setAttribute("aria-activedescendant", element.id);
    if (scroll) element.scrollIntoView({ block: "nearest" });
  }

  function choose(item: ListItem): void {
    item.onSelect();
    options.onChoose?.();
  }

  function render(): void {
    const query = normalize(input.value.trim());
    const nodes: HTMLLIElement[] = [];
    visible = [];
    active = -1;
    let counter = 0;
    for (const group of groups) {
      const matches = group.items.filter((item) => !query || searchText(item).includes(query));
      if (!matches.length) continue;
      if (group.label) {
        const label = document.createElement("li");
        label.className = "list-group";
        label.setAttribute("role", "presentation");
        label.textContent = group.label;
        nodes.push(label);
      }
      for (const item of matches) {
        const element = itemElement(item, `${prefix}-${counter++}`);
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
    setActive(query || current < 0 ? 0 : current, false);
  }

  root.addEventListener("keydown", (event) => {
    switch (event.key) {
      case "ArrowDown":
        setActive(active + 1);
        break;
      case "ArrowUp":
        setActive(active - 1);
        break;
      case "Home":
        if (event.target === input) return;
        setActive(0);
        break;
      case "End":
        if (event.target === input) return;
        setActive(visible.length - 1);
        break;
      case "Enter":
        if (visible[active]) choose(visible[active].item);
        break;
      case "Escape":
        if (!options.onEscape) return;
        options.onEscape();
        break;
      default:
        return;
    }
    event.preventDefault();
    event.stopPropagation();
  });
  input.addEventListener("input", render);

  return {
    root,
    setGroups(next) {
      groups = next;
      render();
    },
    setEmptyText(text) {
      emptyNote.textContent = text;
    },
    focus() {
      (options.search ? input : list).focus();
    },
  };
}

function itemElement(item: ListItem, id: string): HTMLLIElement {
  const element = document.createElement("li");
  element.className = "list-item";
  element.id = id;
  element.setAttribute("role", "option");
  element.setAttribute("aria-selected", "false");
  if (item.current) element.classList.add("is-current");

  const main = document.createElement("span");
  main.className = "list-main";
  if (item.badge) {
    const badge = document.createElement("span");
    badge.className = `list-badge is-${item.badge.tone}`;
    badge.textContent = item.badge.text;
    badge.setAttribute("aria-hidden", "true");
    main.append(badge);
  }
  const title = document.createElement("span");
  title.className = "list-title";
  title.textContent = item.title;
  main.append(title);
  element.append(main);

  if (item.meta) {
    const meta = document.createElement("span");
    meta.className = "list-meta";
    if (item.metaTone) meta.classList.add(`is-${item.metaTone}`);
    meta.textContent = item.meta;
    element.append(meta);
  }
  for (const action of item.actions ?? []) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "list-action";
    button.tabIndex = -1;
    button.textContent = action.label;
    button.title = action.title;
    button.setAttribute("aria-label", action.title);
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      action.run();
    });
    element.append(button);
  }
  if (item.detail) {
    const detail = document.createElement("span");
    detail.className = "list-detail";
    detail.textContent = item.detail;
    element.append(detail);
  }
  return element;
}
