import { clsx } from "clsx";

export default function Input({ label, error, className, id, ...props }) {
  // Auto-generate id from label so <label htmlFor> works for autofill + accessibility
  const inputId = id || (label ? `input-${label.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "")}` : undefined);
  return (
    <div className={className}>
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={clsx(
          "block w-full rounded-lg border px-3 py-2 text-sm shadow-sm transition focus:outline-none focus:ring-2 focus:ring-brand-500",
          error ? "border-red-300 focus:ring-red-500" : "border-gray-300"
        )}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
