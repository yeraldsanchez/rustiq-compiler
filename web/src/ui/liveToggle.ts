/** Errores en vivo: compila tras una pausa al escribir y marca los errores
 *  sin tocar la salida. Se activa desde el riel (botón con un punto verde
 *  cuando está encendido) o desde el interruptor del panel lateral. La
 *  preferencia se recuerda. */

import { dom } from "../dom";
import { KEYS, load, save } from "../storage";

const LIVE_DELAY_MS = 500;

export interface LiveErrors {
  /** Avisa que el código cambió; compila después de la pausa si está activo. */
  notifyChange(): void;
}

export function initLiveErrors(check: () => void): LiveErrors {
  let enabled = load(KEYS.liveErrors) === "1";
  let timer: number | undefined;

  const render = () => {
    dom.railLive.setAttribute("aria-pressed", String(enabled));
    dom.railLive.title = `Errores en vivo: ${enabled ? "encendido" : "apagado"}`;
    dom.liveSwitch.setAttribute("aria-checked", String(enabled));
  };

  const toggle = () => {
    enabled = !enabled;
    save(KEYS.liveErrors, enabled ? "1" : "0");
    render();
    window.clearTimeout(timer);
    if (enabled) check();
  };
  dom.railLive.addEventListener("click", toggle);
  dom.liveSwitch.addEventListener("click", toggle);

  render();
  if (enabled) check();

  return {
    notifyChange() {
      if (!enabled) return;
      window.clearTimeout(timer);
      timer = window.setTimeout(check, LIVE_DELAY_MS);
    },
  };
}
