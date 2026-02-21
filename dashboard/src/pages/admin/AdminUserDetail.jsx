import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useApi } from "../../hooks/useApi";
import { api } from "../../lib/api";
import Card, { CardHeader } from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { useToast } from "../../components/ui/Toast";
import { getBadgeColor } from "../../lib/planConfig";
import { money, date } from "../../lib/format";
import {
  ArrowLeft,
  User,
  CreditCard,
  Activity,
  Shield,
  ShieldOff,
  RefreshCw,
} from "lucide-react";

const PLANS = ["free", "trial", "cazador", "competidor", "dominador"];

export default function AdminUserDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const { data, loading, refetch } = useApi(`/admin/users/${id}`);
  const [changingPlan, setChangingPlan] = useState(false);
  const [togglingAdmin, setTogglingAdmin] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState("");

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  if (!data || data.error) {
    return (
      <div className="text-center py-24">
        <p className="text-gray-500">Usuario no encontrado</p>
        <Button variant="secondary" className="mt-4" onClick={() => navigate("/admin/users")}>
          <ArrowLeft className="h-4 w-4" /> Volver
        </Button>
      </div>
    );
  }

  const { profile: u, subscriptions, payments, activity } = data;

  const handleChangePlan = async () => {
    if (!selectedPlan || selectedPlan === u.plan) return;
    setChangingPlan(true);
    try {
      await api.post(`/admin/users/${id}/change-plan`, { plan: selectedPlan });
      toast.success(`Plan cambiado a ${selectedPlan}`);
      refetch();
    } catch (err) {
      toast.error(err.error || "Error al cambiar plan");
    } finally {
      setChangingPlan(false);
    }
  };

  const handleToggleAdmin = async () => {
    setTogglingAdmin(true);
    try {
      const res = await api.post(`/admin/users/${id}/toggle-admin`);
      toast.success(res.is_admin ? "Ahora es administrador" : "Ya no es administrador");
      refetch();
    } catch (err) {
      toast.error(err.error || "Error al cambiar admin");
    } finally {
      setTogglingAdmin(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="secondary" size="sm" onClick={() => navigate("/admin/users")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex items-center gap-2">
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-brand-400 to-purple-400 text-white flex items-center justify-center text-lg font-bold">
            {u.email?.[0]?.toUpperCase()}
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{u.company_name || u.email}</h1>
            <p className="text-sm text-gray-500">{u.email}</p>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Badge color={getBadgeColor(u.plan) || "gray"}>{u.plan || "free"}</Badge>
          {u.is_admin && <Badge color="red">admin</Badge>}
        </div>
      </div>

      {/* Profile + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile */}
        <Card className="lg:col-span-2">
          <CardHeader title="Perfil" icon={<User className="h-5 w-5 text-brand-600" />} />
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <div>
              <dt className="text-gray-400">ID</dt>
              <dd className="font-mono text-gray-700">#{u.id}</dd>
            </div>
            <div>
              <dt className="text-gray-400">Sector</dt>
              <dd className="text-gray-700">{u.sector || "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-400">Ciudad</dt>
              <dd className="text-gray-700">{u.city || "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-400">Presupuesto</dt>
              <dd className="text-gray-700">
                {u.budget_min || u.budget_max
                  ? `${money(u.budget_min)} – ${money(u.budget_max)}`
                  : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-gray-400">Keywords</dt>
              <dd className="text-gray-700 flex flex-wrap gap-1">
                {(u.keywords || []).length > 0
                  ? u.keywords.map((k, i) => (
                      <span key={i} className="px-2 py-0.5 bg-gray-100 rounded text-xs">
                        {k}
                      </span>
                    ))
                  : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-gray-400">Confianza</dt>
              <dd className="text-gray-700">
                {u.trust_level} ({u.verified_payments_count} pagos verificados)
              </dd>
            </div>
            <div>
              <dt className="text-gray-400">Onboarding</dt>
              <dd className="text-gray-700">{u.onboarding_completed ? "Completado" : "Pendiente"}</dd>
            </div>
            <div>
              <dt className="text-gray-400">Trial expira</dt>
              <dd className="text-gray-700">{u.trial_ends_at ? date(u.trial_ends_at) : "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-400">Politica privacidad</dt>
              <dd className="text-gray-700">{u.privacy_policy_version || "No aceptada"}</dd>
            </div>
            <div>
              <dt className="text-gray-400">Registro</dt>
              <dd className="text-gray-700">{date(u.created_at)}</dd>
            </div>
          </dl>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader title="Acciones" />
          <div className="space-y-4">
            {/* Change plan */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Cambiar plan</label>
              <div className="flex gap-2">
                <select
                  className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  value={selectedPlan || u.plan}
                  onChange={(e) => setSelectedPlan(e.target.value)}
                >
                  {PLANS.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
                <Button
                  size="sm"
                  disabled={changingPlan || !selectedPlan || selectedPlan === u.plan}
                  onClick={handleChangePlan}
                >
                  {changingPlan ? <RefreshCw className="h-4 w-4 animate-spin" /> : "Aplicar"}
                </Button>
              </div>
            </div>

            {/* Toggle admin */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Admin</label>
              <Button
                variant={u.is_admin ? "danger" : "secondary"}
                size="sm"
                className="w-full"
                disabled={togglingAdmin}
                onClick={handleToggleAdmin}
              >
                {u.is_admin ? (
                  <>
                    <ShieldOff className="h-4 w-4" /> Quitar admin
                  </>
                ) : (
                  <>
                    <Shield className="h-4 w-4" /> Hacer admin
                  </>
                )}
              </Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Subscriptions */}
      <Card>
        <CardHeader
          title={`Suscripciones (${subscriptions.length})`}
          icon={<CreditCard className="h-5 w-5 text-brand-600" />}
        />
        {subscriptions.length === 0 ? (
          <p className="text-sm text-gray-400">Sin suscripciones</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Plan</th>
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Estado</th>
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Monto</th>
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Inicio</th>
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Fin</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {subscriptions.map((s) => (
                  <tr key={s.id}>
                    <td className="px-3 py-2">
                      <Badge color={getBadgeColor(s.plan) || "gray"}>{s.plan}</Badge>
                    </td>
                    <td className="px-3 py-2">
                      <Badge
                        color={
                          s.status === "active"
                            ? "green"
                            : s.status === "cancelled"
                              ? "red"
                              : "gray"
                        }
                      >
                        {s.status}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-gray-700">{money(s.amount)}</td>
                    <td className="px-3 py-2 text-gray-500 text-xs">{date(s.starts_at)}</td>
                    <td className="px-3 py-2 text-gray-500 text-xs">{date(s.ends_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Payments */}
      <Card>
        <CardHeader
          title={`Pagos (${payments.length})`}
          icon={<CreditCard className="h-5 w-5 text-green-600" />}
        />
        {payments.length === 0 ? (
          <p className="text-sm text-gray-400">Sin pagos registrados</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">ID</th>
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Monto</th>
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Estado</th>
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Plan</th>
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Ref</th>
                  <th className="text-left px-3 py-2 text-xs font-semibold text-gray-500">Fecha</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {payments.map((p) => (
                  <tr key={p.id}>
                    <td className="px-3 py-2 text-gray-400 font-mono text-xs">#{p.id}</td>
                    <td className="px-3 py-2 text-gray-700">{money(p.amount)}</td>
                    <td className="px-3 py-2">
                      <Badge
                        color={
                          p.status === "approved"
                            ? "green"
                            : p.status === "pending"
                              ? "yellow"
                              : p.status === "declined"
                                ? "red"
                                : "gray"
                        }
                      >
                        {p.status}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-gray-500 text-xs">{p.plan || "—"}</td>
                    <td className="px-3 py-2 text-gray-400 font-mono text-xs truncate max-w-[100px]">
                      {p.reference || "—"}
                    </td>
                    <td className="px-3 py-2 text-gray-500 text-xs">{date(p.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Activity */}
      <Card>
        <CardHeader
          title={`Actividad reciente (${activity.length})`}
          icon={<Activity className="h-5 w-5 text-purple-600" />}
        />
        {activity.length === 0 ? (
          <p className="text-sm text-gray-400">Sin actividad registrada</p>
        ) : (
          <div className="space-y-2">
            {activity.map((a, i) => (
              <div
                key={i}
                className="flex items-center justify-between text-sm py-2 border-b border-gray-50 last:border-0"
              >
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-mono">
                    {a.action}
                  </span>
                  {a.resource && (
                    <span className="text-gray-400 text-xs">
                      {a.resource}
                      {a.resource_id ? ` #${a.resource_id}` : ""}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-400">
                  {a.ip && <span>{a.ip}</span>}
                  <span>{date(a.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
