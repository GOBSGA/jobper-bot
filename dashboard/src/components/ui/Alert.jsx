/**
 * Alert — minimal, no filled backgrounds that blare.
 * Left border accent carries the semantic weight quietly.
 */
export default function Alert({ variant = "error", children }) {
  const styles = {
    error:   "border-l-2 border-red-400   bg-red-50/60   text-red-800",
    success: "border-l-2 border-accent-400 bg-accent-50/60 text-accent-800",
    warning: "border-l-2 border-amber-400 bg-amber-50/60 text-amber-800",
    info:    "border-l-2 border-brand-400  bg-brand-50/60 text-ink-700",
  };

  return (
    <div className={`rounded-xl border border-surface-border p-4 ${styles[variant]}`}>
      <p className="text-sm leading-relaxed">{children}</p>
    </div>
  );
}
