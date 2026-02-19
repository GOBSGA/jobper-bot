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
      <Card>
        <CardHeader title="Distribución por plan" />
        <div className="space-y-2">
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
                  <div className="flex-1 bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-brand-500 h-2 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-gray-700 w-12 text-right">{count}</span>
                  <span className="text-xs text-gray-400 w-8 text-right">{pct}%</span>
                </div>
              );
            })}
          {Object.keys(planCounts).length === 0 && (
            <p className="text-sm text-gray-400">Sin datos aún</p>
          )}
        </div>
      </Card>

      {/* Contracts */}
      <Card>
        <CardHeader title="Contratos" />
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Total en base de datos</span>
            <span className="text-lg font-bold text-gray-900">
              {k.total_contracts?.toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Ingresados hoy</span>
            <span className="font-semibold text-green-700">{k.contracts_today}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Últimos 7 días</span>
            <span className="font-semibold text-gray-700">{k.contracts_7d}</span>
          </div>
          <div className="border-t border-gray-100 pt-3">
            <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">
              Fuentes activas
            </p>
            <div className="grid grid-cols-2 gap-1.5">
              {(scrapers || []).map((s) => (
                <div key={s.key} className="flex items-center gap-1.5">
                  <div
                    className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${
                      !s.enabled
                        ? "bg-gray-300"
                        : s.error_count > 3
                          ? "bg-red-500"
                          : s.error_count > 0
                            ? "bg-yellow-500"
                            : "bg-green-500"
                    }`}
                  />
                  <span className="text-xs text-gray-600 truncate">{s.name}</span>
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
