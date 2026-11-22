/** Elementos de index.html que usa el código. Si falta uno, falla al cargar
 *  con un mensaje claro en vez de fallar más tarde en un clic. */

function byId<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Falta el elemento #${id} en index.html`);
  return element as T;
}

export const dom = {
  examples: byId<HTMLSelectElement>("examples"),
  compileButton: byId<HTMLButtonElement>("btn-compile"),
  runButton: byId<HTMLButtonElement>("btn-run"),
  stopButton: byId<HTMLButtonElement>("btn-stop"),

  banner: byId<HTMLDivElement>("banner"),
  bannerText: byId<HTMLSpanElement>("banner-text"),
  retryButton: byId<HTMLButtonElement>("btn-retry"),

  editor: byId<HTMLDivElement>("editor"),
  liveButton: byId<HTMLButtonElement>("btn-live"),
  splitX: byId<HTMLDivElement>("split-x"),
  splitY: byId<HTMLDivElement>("split-y"),
  cursorPos: byId<HTMLSpanElement>("cursor-pos"),

  statState: byId<HTMLSpanElement>("stat-state"),
  statTime: byId<HTMLSpanElement>("stat-time"),
  statSize: byId<HTMLSpanElement>("stat-size"),

  tabOutput: byId<HTMLButtonElement>("tab-output"),
  tabWat: byId<HTMLButtonElement>("tab-wat"),
  paneOutput: byId<HTMLDivElement>("pane-output"),
  paneWat: byId<HTMLDivElement>("pane-wat"),
  watEmpty: byId<HTMLParagraphElement>("wat-empty"),
  watHost: byId<HTMLDivElement>("wat-host"),
  copyButton: byId<HTMLButtonElement>("btn-copy"),
  downloadWatButton: byId<HTMLButtonElement>("btn-dl-wat"),
  downloadWasmButton: byId<HTMLButtonElement>("btn-dl-wasm"),

  errorCount: byId<HTMLSpanElement>("error-count"),
  errorList: byId<HTMLUListElement>("error-list"),
  errorsEmpty: byId<HTMLParagraphElement>("errors-empty"),
};
