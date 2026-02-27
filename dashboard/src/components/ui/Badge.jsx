import { clsx } from "clsx";

/**
 * Restrained badges — muted tints, no visual weight.
 * Colors signal meaning without shouting.
 */
const colors = {
  blue:   "bg-blue-50   text-blue-600",
  green:  "bg-accent-50  text-accent-700",
  yellow: "bg-amber-50  text-amber-700",
  red:    "bg-red-50    text-red-600",
  gray:   "bg-surface-hover text-ink-600",
  purple: "bg-violet-50 text-violet-600",
  indigo: "bg-brand-50  text-brand-600",
};

export default function Badge({ color = "gray", children, className }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-md px-2 py-0.5 text-2xs font-medium tracking-snug",
        colors[color],
        className
      )}
    >
      {children}
    </span>
  );
}
