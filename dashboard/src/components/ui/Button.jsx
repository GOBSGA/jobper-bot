import { clsx } from "clsx";

const variants = {
  primary:   "bg-brand-500 text-white hover:bg-brand-600 focus:ring-brand-400",
  secondary: "bg-white border border-surface-border text-ink-600 hover:bg-surface-hover focus:ring-brand-300",
  danger:    "bg-white border border-red-200 text-red-600 hover:bg-red-50 focus:ring-red-300",
  ghost:     "text-ink-600 hover:bg-surface-hover focus:ring-brand-300",
};

const sizes = {
  sm: "h-7 px-3 text-xs gap-1.5",
  md: "h-8 px-3.5 text-sm gap-2",
  lg: "h-10 px-5 text-sm gap-2",
};

export default function Button({ variant = "primary", size = "md", className, children, ...props }) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-lg font-medium tracking-snug transition-colors",
        "focus:outline-none focus:ring-2 focus:ring-offset-1",
        "disabled:opacity-40 disabled:pointer-events-none",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
