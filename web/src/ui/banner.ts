/** Aviso de que el servidor de compilación no responde. */

import { dom } from "../dom";

let retry: (() => void) | null = null;

dom.retryButton.addEventListener("click", () => retry?.());

export function showBanner(message: string, onRetry: () => void): void {
  dom.bannerText.textContent = message;
  retry = onRetry;
  dom.banner.hidden = false;
}

export function hideBanner(): void {
  dom.banner.hidden = true;
  retry = null;
}
