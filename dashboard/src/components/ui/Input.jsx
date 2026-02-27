import { clsx } from "clsx";

export default function Input({ label, error, className, id, ...props }) {
  const inputId =
    id ||
    (label
      ? `input-${label.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "")}`
      : undefined);

  return (
    <div className={className}>
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-medium text-ink-600 mb-1.5 tracking-snug"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={clsx(
          "block w-full rounded-xl border bg-white px-3 py-2 text-sm text-ink-900",
          "placeholder:text-ink-400",
          "transition-colors duration-100",
          "focus:outline-none focus:ring-2 focus:ring-brand-200 focus:border-brand-400",
          error
            ? "border-red-300 focus:ring-red-100 focus:border-red-400"
            : "border-surface-border hover:border-ink-200"
        )}
        {...props}
      />
      {error && <p className="mt-1.5 text-xs text-red-500">{error}</p>}
    </div>
  );
}
