import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";

import { cn } from "@/lib/utils";

type ToastKind = "success" | "error" | "info";

interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

interface ToastContextValue {
  notify: (message: string, kind?: ToastKind) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);
let nextId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((items) => items.filter((item) => item.id !== id));
  }, []);

  const notify = useCallback(
    (message: string, kind: ToastKind = "info") => {
      const id = nextId++;
      setToasts((items) => [...items, { id, kind, message }]);
      window.setTimeout(() => dismiss(id), 5000);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex w-[min(92vw,380px)] flex-col gap-2">
        {toasts.map((toast) => {
          const Icon =
            toast.kind === "success" ? CheckCircle2 : toast.kind === "error" ? AlertCircle : Info;
          return (
            <div
              key={toast.id}
              role="status"
              className={cn(
                "flex items-start gap-3 rounded-lg border bg-white p-3 shadow-lg",
                toast.kind === "success" && "border-emerald-200",
                toast.kind === "error" && "border-red-200",
                toast.kind === "info" && "border-blue-200",
              )}
            >
              <Icon
                className={cn(
                  "mt-0.5 h-4 w-4 shrink-0",
                  toast.kind === "success" && "text-emerald-600",
                  toast.kind === "error" && "text-red-600",
                  toast.kind === "info" && "text-blue-600",
                )}
              />
              <p className="flex-1 text-sm text-slate-700">{toast.message}</p>
              <button
                onClick={() => dismiss(toast.id)}
                className="text-slate-400 hover:text-slate-700"
                aria-label="Dismiss notification"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used inside ToastProvider");
  return context;
}
