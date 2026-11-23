/** Cuadro pequeño con un campo de texto junto a un punto de la pantalla:
 *  renombrar un símbolo. Enter aplica, Esc cancela. Si `submit` devuelve un
 *  mensaje, se muestra debajo y el cuadro sigue abierto. */

export interface PromptOptions {
  anchor: DOMRect;
  title: string;
  value: string;
  submit(value: string): string | null;
}

const OFFSET = 6;
const MARGIN = 8;

let close: (() => void) | null = null;

export function openInlinePrompt(options: PromptOptions): void {
  close?.();
  const previousFocus = document.activeElement as HTMLElement | null;

  const root = document.createElement("form");
  root.className = "inline-prompt";
  root.setAttribute("role", "dialog");
  root.setAttribute("aria-label", options.title);

  const title = document.createElement("span");
  title.className = "inline-prompt-title";
  title.textContent = options.title;

  const input = document.createElement("input");
  input.className = "inline-prompt-input";
  input.value = options.value;
  input.spellcheck = false;
  input.autocomplete = "off";
  input.setAttribute("aria-label", options.title);

  const message = document.createElement("p");
  message.className = "inline-prompt-message";
  message.textContent = "Enter para aplicar · Esc para cancelar";

  root.append(title, input, message);

  function finish(restoreFocus: boolean): void {
    if (close !== finishCurrent) return;
    close = null;
    root.remove();
    document.removeEventListener("pointerdown", onPointerDown, true);
    if (restoreFocus) previousFocus?.focus();
  }
  const finishCurrent = () => finish(false);

  function onPointerDown(event: PointerEvent): void {
    if (!root.contains(event.target as Node)) finish(false);
  }

  root.addEventListener("submit", (event) => {
    event.preventDefault();
    const problem = options.submit(input.value.trim());
    if (problem === null) {
      finish(false);
      return;
    }
    message.textContent = problem;
    message.classList.add("is-error");
    input.setAttribute("aria-invalid", "true");
  });
  input.addEventListener("input", () => {
    message.classList.remove("is-error");
    input.removeAttribute("aria-invalid");
  });
  root.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      finish(true);
    }
  });
  document.addEventListener("pointerdown", onPointerDown, true);

  document.body.append(root);
  close = finishCurrent;
  const { anchor } = options;
  const left = Math.min(Math.max(MARGIN, anchor.left - 8), window.innerWidth - root.offsetWidth - MARGIN);
  const below = anchor.bottom + OFFSET;
  const top = below + root.offsetHeight <= window.innerHeight - MARGIN ? below : anchor.top - OFFSET - root.offsetHeight;
  root.style.left = `${Math.max(MARGIN, left)}px`;
  root.style.top = `${Math.max(MARGIN, top)}px`;
  input.focus();
  input.select();
}
