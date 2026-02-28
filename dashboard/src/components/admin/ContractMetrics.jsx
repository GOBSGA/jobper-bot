import Card, { CardHeader } from "../ui/Card";
import Badge from "../ui/Badge";
import { getBadgeColor } from "../../lib/planConfig";

/**
 * Contract metrics - Plan distribution and contract stats
 */
export default function ContractMetrics({ kpis, scrapers }) {
  const k = kpis || {};
  const planOrder = [
    "cazador",
    "competidor",
    "dominador",
    "free",
    "trial",
    "alertas",
    "business",
    "enterprise",
  ];
  const planCounts = k.plan_counts || {};

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Plan distribution */}
      <Card className="p-5 sm:p-6">
        <CardHeader title="Distribución por plan" />
        <div className="space-y-2.5 mt-4">
          {planOrder
            .filter((p) => planCounts[p] > 0)
            .map((plan) => {
              const count = planCounts[plan] || 0;
              const pct = k.total_users > 0 ? Math.round((count / k.total_users) * 100) : 0;
              return (
                <div key={plan} className="flex items-center gap-3">
                  <div className="w-20 flex-shrink-0">
                    <Badge color={getBadgeColor(plan) || "gray"}>{plan}</Badge>
                  </div>
                  <div className="flex-1 bg-surface-hover rounded-full h-2">
                    <div
                      className="bg-brand-500 h-2 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-ink-700 w-10 text-right">{count}</span>
                  <span className="text-xs text-ink-400 w-8 text-right">{pct}%</span>
                </div>
              );
            })}
          {Object.keys(planCounts).length === 0 && (
            <p className="text-sm text-ink-400">Sin datos aún</p>
          )}
        </div>
      </Card>

      {/* Contracts */}
      <Card className="p-5 sm:p-6">
        <CardHeader title="Contratos" />
        <div className="space-y-3 mt-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-ink-600">Total en base de datos</span>
            <span className="text-lg font-bold text-ink-900">
              {k.total_contracts?.toLocaleString() ?? "—"}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-ink-600">Ingresados hoy</span>
            <span className="font-semibold text-accent-700">{k.contracts_today ?? "—"}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-ink-600">Últimos 7 días</span>
            <span className="font-semibold text-ink-700">{k.contracts_7d ?? "—"}</span>
          </div>
          <div className="border-t border-surface-border pt-3">
            <p className="text-xs text-ink-400 mb-2.5 font-medium uppercase tracking-wide">
              Fuentes activas
            </p>
            <div className="grid grid-cols-2 gap-1.5">
              {(scrapers || []).map((s) => (
                <div key={s.key} className="flex items-center gap-1.5">
                  <div
                    className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${
                      !s.enabled
                        ? "bg-surface-border"
                        : s.error_count > 3
                          ? "bg-red-500"
                          : s.error_count > 0
                            ? "bg-amber-500"
                            : "bg-accent-500"
                    }`}
                  />
                  <span className="text-xs text-ink-600 truncate">{s.name}</span>
                  {s.error_count > 0 && (
                    <span className="text-[10px] text-red-500 font-bold ml-auto">
                      {s.error_count}✗
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
