import { useEffect } from "react";
import { X } from "@phosphor-icons/react";

export default function Modal({ open, onClose, title, children }) {
  useEffect(() => {
    if (open) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop — very subtle, not jarring black */}
      <div
        className="fixed inset-0 bg-ink-900/25 backdrop-blur-[2px]"
        onClick={onClose}
      />
      <div className="relative z-10 w-full max-w-lg rounded-2xl bg-white border border-surface-border p-6 shadow-md animate-slide-up">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-sm font-semibold text-ink-900 tracking-snug">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-ink-400 hover:text-ink-600 hover:bg-surface-hover transition-colors"
          >
            <X size={18} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
