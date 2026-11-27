export interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
  prompt(): Promise<void>;
}

type IosNavigator = Navigator & { standalone?: boolean };

export function isStandalone(): boolean {
  if (typeof window === "undefined") return false;
  const displayMode = window.matchMedia?.("(display-mode: standalone)")?.matches ?? false;
  return Boolean(displayMode || (navigator as IosNavigator).standalone);
}

export function isIos(): boolean {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent || "";
  const iPadDesktopMode = navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1;
  return /iPad|iPhone|iPod/i.test(ua) || iPadDesktopMode;
}

export function isIosSafari(): boolean {
  if (!isIos()) return false;
  const ua = navigator.userAgent || "";
  return /Safari/i.test(ua) && !/CriOS|FxiOS|EdgiOS|OPiOS/i.test(ua);
}

/**
 * Register the service worker and notify the app when a new version is waiting.
 *
 * The worker never calls skipWaiting on install, so an open tab keeps working
 * until the user chooses to reload. PwaManager listens for the custom event.
 */
export function registerServiceWorker(): void {
  if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;

  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js", { scope: "/" })
      .then((registration) => {
        const announce = () => {
          if (registration.waiting && navigator.serviceWorker.controller) {
            window.dispatchEvent(
              new CustomEvent("facultyinsight:sw-update", {
                detail: { registration },
              }),
            );
          }
        };

        announce();
        registration.addEventListener("updatefound", () => {
          const worker = registration.installing;
          worker?.addEventListener("statechange", () => {
            if (worker.state === "installed") announce();
          });
        });

        // Check for updates when the user returns to the tab, at most once per
        // page load, so a long-lived installed app does not stay stale.
        document.addEventListener("visibilitychange", () => {
          if (document.visibilityState === "visible") {
            void registration.update().catch(() => undefined);
          }
        });
      })
      .catch(() => {
        // Registration is optional: the web app must keep working without it.
      });
  });
}

export function applyServiceWorkerUpdate(registration: ServiceWorkerRegistration): void {
  let reloaded = false;
  const reload = () => {
    if (reloaded) return;
    reloaded = true;
    window.location.reload();
  };

  navigator.serviceWorker.addEventListener("controllerchange", reload, { once: true });
  registration.waiting?.postMessage({ type: "SKIP_WAITING" });
  // Fallback for browsers that do not fire controllerchange promptly.
  window.setTimeout(reload, 1500);
}
