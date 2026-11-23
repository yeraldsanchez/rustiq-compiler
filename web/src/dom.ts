/** Elementos de index.html que usa el código. Si falta uno, falla al cargar
 *  con un mensaje claro en vez de fallar más tarde en un clic. */

function byId<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Falta el elemento #${id} en index.html`);
  return element as T;
}

export const dom = {
  compileButton: byId<HTMLButtonElement>("btn-compile"),
  runButton: byId<HTMLButtonElement>("btn-run"),
  stopButton: byId<HTMLButtonElement>("btn-stop"),

  banner: byId<HTMLDivElement>("banner"),
  bannerText: byId<HTMLSpanElement>("banner-text"),
  retryButton: byId<HTMLButtonElement>("btn-retry"),

  app: document.querySelector<HTMLElement>(".app")!,
  railLive: byId<HTMLButtonElement>("rail-live"),
  railKeys: byId<HTMLButtonElement>("rail-keys"),
  side: byId<HTMLElement>("side"),
  sideTitle: byId<HTMLHeadingElement>("side-title"),
  sideTools: byId<HTMLDivElement>("side-tools"),
  sideBody: byId<HTMLDivElement>("side-body"),
  sideNewButton: byId<HTMLButtonElement>("btn-side-new"),
  sideOpenButton: byId<HTMLButtonElement>("btn-side-open"),
  liveSwitch: byId<HTMLButtonElement>("live-switch"),
  fileInput: byId<HTMLInputElement>("file-input"),

  editor: byId<HTMLDivElement>("editor"),
  editorHead: byId<HTMLDivElement>("editor-head"),
  editorStatus: byId<HTMLDivElement>("editor-status"),
  fileTabs: byId<HTMLDivElement>("file-tabs"),
  newFileButton: byId<HTMLButtonElement>("btn-new-file"),
  welcome: byId<HTMLDivElement>("welcome"),
  welcomeNew: byId<HTMLButtonElement>("welcome-new"),
  welcomeOpen: byId<HTMLButtonElement>("welcome-open"),
  welcomeExamples: byId<HTMLButtonElement>("welcome-examples"),
  welcomeRecent: byId<HTMLDivElement>("welcome-recent"),
  recentList: byId<HTMLUListElement>("recent-list"),
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
