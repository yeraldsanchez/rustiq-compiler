/** Los archivos abiertos en el editor, cuál está activo y los cerrados hace
 *  poco. Se guardan en el navegador. En la primera visita se arranca con un
 *  archivo; después puede no haber ninguno (el editor muestra el inicio). Aquí solo
 *  viven los datos: las pestañas (ui/fileTabs.ts) los muestran y main.ts
 *  conecta los cambios con el editor. */

import { KEYS, load, remove, save } from "./storage";

export interface SourceFile {
  id: string;
  name: string;
  source: string;
}

export interface ClosedFile extends SourceFile {
  /** Posición que tenía entre las pestañas. */
  index: number;
  closedAt: number;
}

export const EXTENSION = ".rq";
const SAVE_DELAY_MS = 300;
const MAX_NAME = 60;
const NAME_CHARS = /^[\w.\- ]+$/;
const MAX_CLOSED = 5;

type Listener = () => void;

let files: SourceFile[] = [];
let closed: ClosedFile[] = [];
let activeId = "";
let saveTimer: number | undefined;
const listeners: Listener[] = [];

function newId(): string {
  return `f${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

function persist(): void {
  window.clearTimeout(saveTimer);
  saveTimer = window.setTimeout(() => {
    save(KEYS.files, JSON.stringify(files));
    save(KEYS.activeFile, activeId);
    save(KEYS.closedFiles, JSON.stringify(closed));
  }, SAVE_DELAY_MS);
}

function changed(): void {
  persist();
  for (const listener of listeners) listener();
}

function isFile(value: unknown): value is SourceFile {
  const f = value as SourceFile;
  return typeof f?.id === "string" && typeof f.name === "string" && typeof f.source === "string";
}

function loadList<T extends SourceFile>(key: string, check: (value: unknown) => value is T): T[] {
  try {
    const parsed: unknown = JSON.parse(load(key) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter(check) : [];
  } catch {
    return [];
  }
}

function isClosed(value: unknown): value is ClosedFile {
  const f = value as ClosedFile;
  return isFile(value) && typeof f.index === "number" && typeof f.closedAt === "number";
}

/** Carga lo guardado. `fallback` da el primer archivo si no hay ninguno. */
export function initFiles(fallback: () => { name: string; source: string }): void {
  files = loadList(KEYS.files, isFile);
  closed = loadList(KEYS.closedFiles, isClosed);
  // Sin nada guardado es la primera visita. Una lista vacía guardada es que
  // se cerraron todos, y así se respeta.
  const firstVisit = load(KEYS.files) === null;
  if (firstVisit) {
    // El editor de antes guardaba un único archivo.
    const legacy = load(KEYS.source);
    const first = legacy !== null ? { name: `main${EXTENSION}`, source: legacy } : fallback();
    files = [{ id: newId(), ...first }];
    remove(KEYS.source);
  }
  const savedActive = load(KEYS.activeFile);
  activeId = files.some((f) => f.id === savedActive) ? savedActive! : (files[0]?.id ?? "");
  persist();
}

export function onFilesChange(listener: Listener): void {
  listeners.push(listener);
}

export const allFiles = (): readonly SourceFile[] => files;
export const activeFile = (): SourceFile | null => files.find((f) => f.id === activeId) ?? files[0] ?? null;
export const recentlyClosed = (): readonly ClosedFile[] => closed;
export const findFile = (id: string): SourceFile | undefined => files.find((f) => f.id === id);
export const findByName = (name: string): SourceFile | undefined => files.find((f) => f.name === name);

export function setActive(id: string): void {
  if (id === activeId || !findFile(id)) return;
  activeId = id;
  changed();
}

/** El texto cambió: se guarda sin avisar a nadie (las pestañas no cambian). */
export function updateSource(id: string, source: string): void {
  const file = findFile(id);
  if (!file) return;
  file.source = source;
  persist();
}

/** `ejemplo.rq` → `ejemplo-2.rq` si ya existe. */
export function uniqueName(name: string, except?: string): string {
  const base = name.endsWith(EXTENSION) ? name.slice(0, -EXTENSION.length) : name;
  const taken = (candidate: string) => files.some((f) => f.name === candidate && f.id !== except);
  let candidate = `${base}${EXTENSION}`;
  for (let n = 2; taken(candidate); n++) candidate = `${base}-${n}${EXTENSION}`;
  return candidate;
}

/** Agrega un archivo (al final o en `index`) y lo deja activo. */
export function addFile(name: string, source: string, index = files.length, id = newId()): SourceFile {
  const file = { id, name: uniqueName(name), source };
  files.splice(Math.min(index, files.length), 0, file);
  activeId = file.id;
  changed();
  return file;
}

/** Cierra un archivo y lo guarda entre los cerrados hace poco. */
export function removeFile(id: string): SourceFile | null {
  const index = files.findIndex((f) => f.id === id);
  if (index < 0) return null;
  const [file] = files.splice(index, 1);
  closed = [{ ...file, index, closedAt: Date.now() }, ...closed.filter((c) => c.id !== id)].slice(0, MAX_CLOSED);
  if (activeId === id) activeId = files[Math.min(index, files.length - 1)]?.id ?? "";
  changed();
  return file;
}

/** Vuelve a abrir un archivo cerrado, en la posición que tenía. */
export function reopenFile(id: string): SourceFile | null {
  const entry = closed.find((c) => c.id === id);
  if (!entry) return null;
  closed = closed.filter((c) => c.id !== id);
  return addFile(entry.name, entry.source, entry.index, entry.id);
}

/** Devuelve un mensaje si el nombre no sirve; si sirve, renombra. */
export function renameFile(id: string, rawName: string): string | null {
  const trimmed = rawName.trim();
  if (!trimmed) return "El nombre no puede quedar vacío.";
  const name = trimmed.endsWith(EXTENSION) ? trimmed : `${trimmed}${EXTENSION}`;
  if (name.length > MAX_NAME) return "El nombre es demasiado largo.";
  if (!NAME_CHARS.test(name)) return "Usa letras, dígitos, espacios, punto, guion o _.";
  if (files.some((f) => f.name === name && f.id !== id)) return `Ya hay un archivo llamado ${name}.`;
  const file = findFile(id);
  if (!file || file.name === name) return null;
  file.name = name;
  changed();
  return null;
}
