import { useEffect, useRef, useState } from "react";
import { Download, RefreshCw, Share2 } from "lucide-react";

import { Button, Modal } from "@/components/ui";
import {
  applyServiceWorkerUpdate,
  isIosSafari,
  isStandalone,
  type BeforeInstallPromptEvent,
} from "@/lib/pwa";

const DISMISS_KEY = "facultyinsight.install-dismissed";

function readDismissed(): boolean {
  try {
    return localStorage.getItem(DISMISS_KEY) === "1";
  } catch {
    return false;
  }
}

export function PwaManager() {
  const promptRef = useRef<BeforeInstallPromptEvent | null>(null);
  const [canInstall, setCanInstall] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [update, setUpdate] = useState<ServiceWorkerRegistration | null>(null);
  const [dismissed, setDismissed] = useState(readDismissed);
  const [ios] = useState(() => isIosSafari() && !isStandalone());

  const dismiss = () => {
    setDismissed(true);
    try {
      localStorage.setItem(DISMISS_KEY, "1");
    } catch {
      // Private browsing may block storage; the banner still hides for this page.
    }
  };

  const promptInstall = async () => {
    const event = promptRef.current;
    if (!event) {
      setHelpOpen(true);
      return;
    }
    await event.prompt();
    const choice = await event.userChoice;
    promptRef.current = null;
    setCanInstall(false);
    if (choice.outcome === "accepted") dismiss();
  };

  useEffect(() => {
    const onPrompt = (event: Event) => {
      event.preventDefault();
      promptRef.current = event as BeforeInstallPromptEvent;
      setCanInstall(true);
    };
    const onInstalled = () => {
      promptRef.current = null;
      setCanInstall(false);
      dismiss();
    };
    const onUpdate = (event: Event) => {
      const detail = (event as CustomEvent<{ registration?: ServiceWorkerRegistration }>).detail;
      if (detail?.registration) setUpdate(detail.registration);
    };
    const onInstallRequest = () => {
      if (promptRef.current) {
        void promptInstall();
      } else {
        setHelpOpen(true);
      }
    };

    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    window.addEventListener("facultyinsight:sw-update", onUpdate);
    window.addEventListener("facultyinsight:install-request", onInstallRequest);
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
      window.removeEventListener("facultyinsight:sw-update", onUpdate);
      window.removeEventListener("facultyinsight:install-request", onInstallRequest);
    };
    // promptInstall only reads refs and state setters, so the listeners stay stable.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const showInstall = !dismissed && !isStandalone() && (canInstall || ios);

  if (!update && !showInstall && !helpOpen) return null;

  return (
    <>
      <div className="pointer-events-none fixed inset-x-3 bottom-3 z-50 flex flex-col items-stretch gap-2 sm:inset-x-auto sm:bottom-4 sm:right-4 sm:w-[22rem] sm:items-end">
        {update ? (
          <div
            className="pointer-events-auto w-full rounded-xl border border-teal-200 bg-white p-4 shadow-academic"
            role="status"
            aria-live="polite"
          >
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-teal-50 p-2 text-teal-700">
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-900">A new version is ready</p>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">
                  Reload to use the latest improvements. Your saved work is not affected.
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button size="sm" onClick={() => applyServiceWorkerUpdate(update)}>
                    Reload
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setUpdate(null)}>
                    Later
                  </Button>
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {showInstall ? (
          <div
            className="pointer-events-auto w-full rounded-xl border border-slate-200 bg-white p-4 shadow-academic"
            role="region"
            aria-label="Install FacultyInsight AI"
          >
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-primary p-2 text-white">
                <Download className="h-4 w-4" aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-900">Install FacultyInsight AI</p>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">
                  {ios
                    ? "Add the app to your Home Screen for a full-screen, app-like experience."
                    : "Open it from your home screen or desktop with one tap. It stays a secure web app."}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {canInstall ? (
                    <Button size="sm" onClick={() => void promptInstall()}>
                      Install
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      icon={<Share2 className="h-3.5 w-3.5" />}
                      onClick={() => setHelpOpen(true)}
                    >
                      How to install
                    </Button>
                  )}
                  <Button size="sm" variant="ghost" onClick={dismiss}>
                    Not now
                  </Button>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      <Modal
        open={helpOpen}
        title="Install FacultyInsight AI"
        description="FacultyInsight AI is a secure web app. It is not a native APK or an App Store download."
        onClose={() => setHelpOpen(false)}
        footer={
          <Button variant="outline" onClick={() => setHelpOpen(false)}>
            Close
          </Button>
        }
      >
        {ios ? (
          <ol className="list-decimal space-y-3 pl-5 text-sm leading-relaxed text-slate-700">
            <li>Open this site in Safari.</li>
            <li>
              Tap the <strong>Share</strong> button in the Safari toolbar.
            </li>
            <li>
              Choose <strong>Add to Home Screen</strong>.
            </li>
            <li>
              Tap <strong>Add</strong>. The app opens in standalone mode from your Home Screen.
            </li>
          </ol>
        ) : (
          <div className="space-y-3 text-sm leading-relaxed text-slate-700">
            <p>
              In Chrome or Edge, open the browser menu and choose{" "}
              <strong>Install app</strong> or <strong>Add to Home screen</strong>. On desktop,
              the install icon may also appear in the address bar.
            </p>
            <p>
              Installation requires HTTPS in production, or localhost during development. If
              the option is missing, your browser or device does not support installation.
            </p>
            <p className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
              The app still works in a normal browser tab. Offline pages are limited to the
              app shell; feedback and reports always need a live connection.
            </p>
          </div>
        )}
      </Modal>
    </>
  );
}
