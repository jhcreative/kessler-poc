// One coalesced toast, fixed bottom-centre, over the page without moving it (PQ-14, PQ-12). A success leaves after
// 5 s, paused while the pointer or focus is on it; an error stays until dismissed.
import { createContext, use, useCallback, useEffect, useRef, useState, type ReactNode } from "react";

interface Toast {
  text: string;
  error: boolean;
}

const ToastContext = createContext<(text: string, error?: boolean) => void>(() => undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<Toast | null>(null);
  const [held, setHeld] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  const show = useCallback((text: string, error = false) => setToast({ text, error }), []);
  useEffect(() => {
    window.clearTimeout(timer.current);
    if (toast && !toast.error && !held) timer.current = window.setTimeout(() => setToast(null), 5000);
    return () => window.clearTimeout(timer.current);
  }, [toast, held]);
  return (
    <ToastContext value={show}>
      {children}
      <div className="toast-slot" aria-live="polite">
        {toast && (
          <div
            className="toast"
            data-error={toast.error || undefined}
            role={toast.error ? "alert" : "status"}
            onPointerEnter={() => setHeld(true)}
            onPointerLeave={() => setHeld(false)}
            onFocus={() => setHeld(true)}
            onBlur={() => setHeld(false)}
          >
            <span>{toast.text}</span>
            <button type="button" className="link-button" onClick={() => setToast(null)}>
              Dismiss
            </button>
          </div>
        )}
      </div>
    </ToastContext>
  );
}

export const useToast = () => use(ToastContext);
