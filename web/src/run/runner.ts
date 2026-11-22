/** Lanza un Worker por ejecución y lo termina al acabar, al pasar el tiempo
 *  límite o al presionar Detener. Un Worker nuevo cada vez garantiza que no
 *  quede estado de la ejecución anterior. */

import type { WorkerMessage } from "./protocol";

export const TIME_LIMIT_MS = 5_000;

export type RunResult =
  | { status: "ok"; elapsedMs: number }
  | { status: "trap"; message: string }
  | { status: "error"; message: string }
  | { status: "limit" }
  | { status: "timeout" }
  | { status: "stopped" };

export interface RunHandlers {
  onPrint(text: string): void;
  onFinish(result: RunResult): void;
}

export class Runner {
  private worker: Worker | null = null;
  private timer: number | undefined;
  private handlers: RunHandlers | null = null;

  get running(): boolean {
    return this.worker !== null;
  }

  run(wasm: Uint8Array<ArrayBuffer>, handlers: RunHandlers): void {
    this.stop();
    this.handlers = handlers;
    const started = performance.now();
    const worker = new Worker(new URL("./worker.ts", import.meta.url), { type: "module" });
    this.worker = worker;

    worker.onmessage = (event: MessageEvent<WorkerMessage>) => {
      const message = event.data;
      switch (message.kind) {
        case "print":
          handlers.onPrint(message.text);
          break;
        case "done":
          this.finish({ status: "ok", elapsedMs: performance.now() - started });
          break;
        case "trap":
          this.finish({ status: "trap", message: message.message });
          break;
        case "error":
          this.finish({ status: "error", message: message.message });
          break;
        case "limit":
          this.finish({ status: "limit" });
          break;
      }
    };
    worker.onerror = (event) => {
      event.preventDefault();
      this.finish({ status: "error", message: event.message || "El Worker falló al iniciar." });
    };

    this.timer = window.setTimeout(() => this.finish({ status: "timeout" }), TIME_LIMIT_MS);
    // Se transfiere una copia: el original sigue disponible para descargarlo.
    const copy = wasm.slice().buffer;
    worker.postMessage({ wasm: copy }, [copy]);
  }

  stop(): void {
    if (this.worker) this.finish({ status: "stopped" });
  }

  private finish(result: RunResult): void {
    window.clearTimeout(this.timer);
    this.worker?.terminate();
    this.worker = null;
    const handlers = this.handlers;
    this.handlers = null;
    handlers?.onFinish(result);
  }
}
