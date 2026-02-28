import Card from "../ui/Card";

/**
 * Reusable KPI card for admin dashboard
 */
export default function KpiCard({ label, value, sub, icon: Icon, color = "brand", urgent }) {
  const colors = {
    brand: "text-brand-600 bg-brand-50",
    green: "text-accent-600 bg-accent-50",
    purple: "text-purple-600 bg-purple-50",
    yellow: "text-amber-600 bg-amber-50",
    red: "text-red-600 bg-red-50",
    gray: "text-ink-400 bg-surface-hover",
    blue: "text-blue-600 bg-blue-50",
  };

  return (
    <Card className={`relative p-4 sm:p-5 ${urgent ? "ring-2 ring-red-300" : ""}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium text-ink-400 uppercase tracking-wide truncate">
            {label}
          </p>
          <p className="text-xl sm:text-2xl font-bold text-ink-900 mt-1 truncate">
            {value ?? "—"}
          </p>
          {sub && <p className="text-xs text-ink-400 mt-0.5 truncate">{sub}</p>}
        </div>
        <div className={`p-2.5 rounded-xl flex-shrink-0 ${colors[color]}`}>
          <Icon size={18} weight="duotone" />
        </div>
      </div>
      {urgent && (
        <div className="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 animate-pulse" />
      )}
    </Card>
  );
}
