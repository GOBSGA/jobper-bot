import { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle, XCircle, WarningCircle, Info, X } from "@phosphor-icons/react";

const ToastCtx = createContext(null);

const configs = {
  success: {
    Icon: CheckCircle,
    style: "bg-white border-accent-200 text-ink-900",
    dot:   "bg-accent-500",
  },
  error: {
    Icon: XCircle,
    style: "bg-white border-red-200 text-ink-900",
    dot:   "bg-red-500",
  },
  warning: {
    Icon: WarningCircle,
    style: "bg-white border-amber-200 text-ink-900",
    dot:   "bg-amber-500",
  },
  info: {
    Icon: Info,
    style: "bg-white border-brand-200 text-ink-900",
    dot:   "bg-brand-400",
  },
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = "info", duration = 4000) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    if (duration > 0) {
      setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), duration);
    }
  }, []);

  const toast = {
    success: (msg) => addToast(msg, "success"),
    error:   (msg) => addToast(msg, "error", 6000),
    warning: (msg) => addToast(msg, "warning"),
    info:    (msg) => addToast(msg, "info"),
  };

  const dismiss = (id) => setToasts((prev) => prev.filter((t) => t.id !== id));

  return (
    <ToastCtx.Provider value={toast}>
      {children}
      <div className="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 max-w-xs w-full pointer-events-none">
        {toasts.map((t) => {
          const { Icon, style, dot } = configs[t.type];
          return (
            <div
              key={t.id}
              className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-2xl border shadow-md animate-slide-up ${style}`}
            >
              {/* Color dot */}
              <span className={`h-2 w-2 rounded-full flex-shrink-0 ${dot}`} />
              <p className="text-sm font-medium flex-1 leading-snug">{t.message}</p>
              <button
                onClick={() => dismiss(t.id)}
                className="flex-shrink-0 p-1 rounded-lg text-ink-400 hover:text-ink-600 hover:bg-surface-hover transition-colors"
              >
                <X size={14} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);
