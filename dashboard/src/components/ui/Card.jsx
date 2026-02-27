import { clsx } from "clsx";

/**
 * Immaculate surface — zero shadow, single hairline border.
 * Content breathes; container recedes into background.
 */
export default function Card({ className, children, ...props }) {
  return (
    <div
      className={clsx(
        "rounded-2xl border border-surface-border bg-white",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, action, children }) {
  return (
    <div className="flex items-center justify-between mb-5">
      <h3 className="text-sm font-semibold text-ink-900 tracking-snug">{title}</h3>
      {action}
      {children}
    </div>
  );
}
