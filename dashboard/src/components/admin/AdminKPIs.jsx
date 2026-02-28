import KpiCard from "./KpiCard";
import { money } from "../../lib/format";
import {
  CurrencyDollar,
  TrendUp,
  CreditCard,
  Warning,
  Users,
  ChartLine,
  UserPlus,
  XCircle,
  Eye,
} from "@phosphor-icons/react";

/**
 * Admin dashboard KPIs - Revenue and Users sections
 */
export default function AdminKPIs({ kpis }) {
  const k = kpis || {};

  return (
    <>
      {/* Revenue KPIs */}
      <div>
        <h2 className="text-xs font-semibold text-ink-400 uppercase tracking-widest mb-3">
          Ingresos
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <KpiCard
            label="MRR"
            value={money(k.mrr)}
            sub="Ingresos mensuales recurrentes"
            icon={CurrencyDollar}
            color="green"
          />
          <KpiCard
            label="ARR"
            value={money(k.arr)}
            sub="Proyección anual"
            icon={TrendUp}
            color="green"
          />
          <KpiCard
            label="Ingresos 30d"
            value={money(k.revenue_30d)}
            sub="Pagos aprobados"
            icon={CreditCard}
            color="brand"
          />
          <KpiCard
            label="Pagos pendientes"
            value={k.pending_payments}
            sub="Requieren revisión"
            icon={Warning}
            color={k.pending_payments > 0 ? "red" : "gray"}
            urgent={k.pending_payments > 0}
          />
        </div>
      </div>

      {/* Users KPIs */}
      <div>
        <h2 className="text-xs font-semibold text-ink-400 uppercase tracking-widest mb-3">
          Usuarios
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <KpiCard label="Total usuarios" value={k.total_users} icon={Users} color="brand" />
          <KpiCard
            label="Activos hoy"
            value={k.active_today}
            sub="Con actividad"
            icon={Eye}
            color="green"
          />
          <KpiCard
            label="Suscriptores"
            value={k.active_paid}
            sub={k.grace_subs > 0 ? `+ ${k.grace_subs} en gracia` : undefined}
            icon={ChartLine}
            color="purple"
          />
          <KpiCard
            label="Nuevos hoy"
            value={k.new_today}
            sub={`${k.new_7d} sem · ${k.new_30d} mes`}
            icon={UserPlus}
            color="green"
          />
          <KpiCard
            label="Churn 30d"
            value={k.churn_30d}
            sub="Cancelaciones"
            icon={XCircle}
            color={k.churn_30d > 0 ? "red" : "gray"}
          />
        </div>
      </div>
    </>
  );
}
