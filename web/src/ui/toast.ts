/** Aviso breve en la esquina inferior: confirma una acción (renombrar,
 *  cerrar un archivo) y, si se puede, ofrece deshacerla. */

export interface ToastAction {
  label: string;
  run(): void;
}

const VISIBLE_MS = 5_000;

let current: { element: HTMLElement; timer: number } | null = null;

function dismiss(): void {
  if (!current) return;
  window.clearTimeout(current.timer);
  current.element.remove();
  current = null;
}

export function showToast(message: string, action?: ToastAction): void {
  dismiss();
  const element = document.createElement("div");
  element.className = "toast";
  element.setAttribute("role", "status");

  const text = document.createElement("p");
  text.textContent = message;
  element.append(text);

  if (action) {
    const button = document.createElement("button");
    button.className = "btn btn-sm";
    button.textContent = action.label;
    button.addEventListener("click", () => {
      dismiss();
      action.run();
    });
    element.append(button);
  }

  document.body.append(element);
  const timer = window.setTimeout(dismiss, VISIBLE_MS);
  current = { element, timer };
  // Mientras el mouse está encima, no se va.
  element.addEventListener("mouseenter", () => window.clearTimeout(current?.timer));
  element.addEventListener("mouseleave", () => {
    if (current?.element === element) current.timer = window.setTimeout(dismiss, VISIBLE_MS);
  });
}
