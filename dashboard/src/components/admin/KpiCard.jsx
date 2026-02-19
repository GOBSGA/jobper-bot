import Card from "../ui/Card";

/**
 * Reusable KPI card for admin dashboard
 */
export default function KpiCard({ label, value, sub, icon: Icon, color = "brand", urgent }) {
  const colors = {
    brand: "text-brand-600 bg-brand-50",
    green: "text-green-600 bg-green-50",
    purple: "text-purple-600 bg-purple-50",
    yellow: "text-yellow-600 bg-yellow-50",
    red: "text-red-600 bg-red-50",
    gray: "text-gray-500 bg-gray-50",
    blue: "text-blue-600 bg-blue-50",
  };

  return (
    <Card className={`relative ${urgent ? "ring-2 ring-red-300" : ""}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value ?? "—"}</p>
          {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
        </div>
        <div className={`p-2.5 rounded-xl ${colors[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      {urgent && (
        <div className="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 animate-pulse" />
      )}
    </Card>
  );
}
