import { clsx } from "clsx";

export default function Card({ className, children, ...props }) {
  return (
    <div className={clsx("rounded-xl border border-gray-200 bg-white p-6 shadow-sm", className)} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ title, action, children }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      {action}
      {children}
    </div>
  );
}
