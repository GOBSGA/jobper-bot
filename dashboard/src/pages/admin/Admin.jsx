import { useApi } from "../../hooks/useApi";
import Card, { CardHeader } from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Spinner from "../../components/ui/Spinner";
import { money } from "../../lib/format";
import { Shield, Users, DollarSign, Activity, Database } from "lucide-react";

export default function Admin() {
  const { data: kpis, loading } = useApi("/admin/dashboard");
  const { data: health } = useApi("/admin/health");

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;

  const k = kpis || {};
  const h = health || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Shield className="h-6 w-6 text-brand-600" />
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "MRR", value: money(k.mrr), icon: DollarSign, color: "text-green-600" },
          { label: "Usuarios totales", value: k.total_users, icon: Users, color: "text-brand-600" },
          { label: "Usuarios activos", value: k.active_users, icon: Activity, color: "text-purple-600" },
          { label: "Contratos hoy", value: k.contracts_today, icon: Database, color: "text-yellow-600" },
        ].map((s) => (
          <Card key={s.label} className="flex items-center gap-4">
            <s.icon className={`h-8 w-8 ${s.color}`} />
            <div>
              <p className="text-xs text-gray-500">{s.label}</p>
              <p className="text-lg font-bold text-gray-900">{s.value ?? "—"}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* System Health */}
      <Card>
        <CardHeader title="Estado del sistema" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(h.services || {}).map(([name, status]) => (
            <div key={name} className="flex items-center gap-2">
              <div className={`h-2.5 w-2.5 rounded-full ${status === "healthy" ? "bg-green-500" : "bg-red-500"}`} />
              <span className="text-sm text-gray-700 capitalize">{name}</span>
              <Badge color={status === "healthy" ? "green" : "red"}>{status}</Badge>
            </div>
          ))}
        </div>
      </Card>

      {/* Churn */}
      {k.churn_rate != null && (
        <Card>
          <CardHeader title="Métricas" />
          <div className="grid grid-cols-3 gap-4 text-center">
            <div><p className="text-2xl font-bold">{k.churn_rate}%</p><p className="text-xs text-gray-500">Churn rate</p></div>
            <div><p className="text-2xl font-bold">{k.trial_users}</p><p className="text-xs text-gray-500">En trial</p></div>
            <div><p className="text-2xl font-bold">{k.paid_users}</p><p className="text-xs text-gray-500">Pagando</p></div>
          </div>
        </Card>
      )}
    </div>
  );
}
