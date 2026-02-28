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
  ShieldCheck,
  ShieldSlash,
  ArrowsClockwise,
  EnvelopeSimple,
  CalendarPlus,
  Warning,
  CheckCircle,
  XCircle,
  Clock,
  ChartLine,
} from "@phosphor-icons/react";

const PLANS = ["free", "trial", "cazador", "competidor", "dominador"];

const STATUS_COLORS = {
  approved: "green",
  pending: "yellow",
  review: "yellow",
  grace: "blue",
  rejected: "red",
  declined: "red",
};

export default function AdminUserDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const { data, loading, error, refetch } = useApi(`/admin/users/${id}`);
  const [changingPlan, setChangingPlan] = useState(false);
  const [togglingAdmin, setTogglingAdmin] = useState(false);
  const [sendingLink, setSendingLink] = useState(false);
  const [extendingTrial, setExtendingTrial] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState("");

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  if (!data || data.error || error) {
    const msg = data?.error || error?.error || "No se pudo cargar el usuario.";
    return (
      <div className="text-center py-24 space-y-4">
        <Warning size={40} className="text-amber-400 mx-auto" weight="duotone" />
        <p className="text-ink-600 font-medium">{msg}</p>
        <p className="text-xs text-ink-400">ID: {id}</p>
        <div className="flex gap-2 justify-center">
          <Button variant="secondary" onClick={refetch}>
            <ArrowsClockwise size={15} /> Reintentar
          </Button>
          <Button variant="secondary" onClick={() => navigate("/admin/users")}>
            <ArrowLeft size={15} /> Volver
          </Button>
        </div>
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

  const handleSendMagicLink = async () => {
    setSendingLink(true);
    try {
      await api.post(`/admin/users/${id}/send-magic-link`);
      toast.success(`Magic link enviado a ${u.email}`);
    } catch (err) {
      toast.error(err.error || "Error al enviar magic link");
    } finally {
      setSendingLink(false);
    }
  };

  const handleExtendTrial = async (days) => {
    setExtendingTrial(true);
    try {
      const res = await api.post(`/admin/users/${id}/extend-trial`, { days });
      toast.success(`Trial extendido hasta ${new Date(res.trial_ends_at).toLocaleDateString("es-CO")}`);
      refetch();
    } catch (err) {
      toast.error(err.error || "Error al extender trial");
    } finally {
      setExtendingTrial(false);
    }
  };

  return (
    <div className="space-y-5 pb-8">
      {/* Header */}
      <div className="flex items-center gap-3 flex-wrap">
        <Button variant="secondary" size="sm" onClick={() => navigate("/admin/users")}>
          <ArrowLeft size={15} />
        </Button>
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-brand-400 to-purple-400 text-white flex items-center justify-center text-lg font-bold flex-shrink-0">
            {u.email?.[0]?.toUpperCase()}
          </div>
          <div className="min-w-0">
            <h1 className="text-lg sm:text-xl font-bold text-ink-900 truncate">
              {u.company_name || u.email}
            </h1>
            <p className="text-sm text-ink-400 truncate">{u.email}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge color={getBadgeColor(u.plan) || "gray"}>{u.plan || "free"}</Badge>
          {u.is_admin && <Badge color="red">admin</Badge>}
        </div>
      </div>

      {/* Profile + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Profile */}
        <Card className="lg:col-span-2 p-5 sm:p-6">
          <div className="flex items-center gap-2 mb-4">
            <User size={16} className="text-brand-600" weight="duotone" />
            <h2 className="font-semibold text-ink-900">Perfil</h2>
          </div>
          <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3 text-sm">
            <div>
              <dt className="text-xs text-ink-400 mb-0.5">ID</dt>
              <dd className="font-mono text-ink-700">#{u.id}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-400 mb-0.5">Sector</dt>
              <dd className="text-ink-700">{u.sector || "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-400 mb-0.5">Ciudad</dt>
              <dd className="text-ink-700">{u.city || "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-400 mb-0.5">Presupuesto</dt>
              <dd className="text-ink-700">
                {u.budget_min || u.budget_max
                  ? `${money(u.budget_min)} – ${money(u.budget_max)}`
                  : "—"}
              </dd>
            </div>
            <div className="col-span-2 sm:col-span-1">
              <dt className="text-xs text-ink-400 mb-0.5">Keywords</dt>
              <dd className="flex flex-wrap gap-1">
                {(u.keywords || []).length > 0
                  ? u.keywords.map((k, i) => (
                      <span key={i} className="px-2 py-0.5 bg-surface-hover rounded-lg text-xs text-ink-600">
                        {k}
                      </span>
                    ))
                  : <span className="text-ink-400">—</span>}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-ink-400 mb-0.5">Confianza</dt>
              <dd className="text-ink-700">
                {u.trust_level} <span className="text-ink-400">({u.verified_payments_count} pagos)</span>
              </dd>
            </div>
            <div>
              <dt className="text-xs text-ink-400 mb-0.5">Onboarding</dt>
              <dd className="text-ink-700">{u.onboarding_completed ? "Completado ✓" : "Pendiente"}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-400 mb-0.5">Trial expira</dt>
              <dd className="text-ink-700">{u.trial_ends_at ? date(u.trial_ends_at) : "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-400 mb-0.5">Política privacidad</dt>
              <dd className="text-ink-700">{u.privacy_policy_version || "No aceptada"}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-400 mb-0.5">Registro</dt>
              <dd className="text-ink-700">{date(u.created_at)}</dd>
            </div>
          </dl>
        </Card>

        {/* Quick Actions */}
        <Card className="p-5 sm:p-6">
          <h2 className="font-semibold text-ink-900 mb-4">Acciones admin</h2>
          <div className="space-y-4">
            {/* Change plan */}
            <div>
              <label className="block text-xs font-medium text-ink-400 mb-1.5">Cambiar plan</label>
              <div className="flex gap-2">
                <select
                  className="flex-1 border border-surface-border rounded-xl px-3 py-2 text-sm text-ink-900 bg-white focus:outline-none focus:border-brand-400"
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
                  {changingPlan ? <ArrowsClockwise size={14} className="animate-spin" /> : "Aplicar"}
                </Button>
              </div>
            </div>

            {/* Extend trial */}
            <div>
              <label className="block text-xs font-medium text-ink-400 mb-1.5">Extender trial</label>
              <div className="flex gap-1.5">
                {[7, 14, 30].map((d) => (
                  <button
                    key={d}
                    onClick={() => handleExtendTrial(d)}
                    disabled={extendingTrial}
                    className="flex-1 py-1.5 text-xs font-medium rounded-lg border border-surface-border hover:border-brand-400 hover:bg-brand-50 hover:text-brand-700 text-ink-600 transition disabled:opacity-50"
                  >
                    <CalendarPlus size={11} className="inline mr-0.5 -mt-0.5" /> +{d}d
                  </button>
                ))}
              </div>
            </div>

            {/* Send magic link */}
            <div>
              <label className="block text-xs font-medium text-ink-400 mb-1.5">Acceso directo</label>
              <Button
                variant="secondary"
                size="sm"
                className="w-full"
                disabled={sendingLink}
                onClick={handleSendMagicLink}
              >
                {sendingLink ? (
                  <><ArrowsClockwise size={14} className="animate-spin" /> Enviando...</>
                ) : (
                  <><EnvelopeSimple size={14} /> Enviar magic link</>
                )}
              </Button>
            </div>

            {/* Toggle admin */}
            <div>
              <label className="block text-xs font-medium text-ink-400 mb-1.5">Permisos</label>
              <Button
                variant={u.is_admin ? "danger" : "secondary"}
                size="sm"
                className="w-full"
                disabled={togglingAdmin}
                onClick={handleToggleAdmin}
              >
                {u.is_admin ? (
                  <><ShieldSlash size={14} /> Quitar admin</>
                ) : (
                  <><ShieldCheck size={14} /> Hacer admin</>
                )}
              </Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Subscriptions */}
      <Card className="p-5 sm:p-6">
        <div className="flex items-center gap-2 mb-4">
          <CreditCard size={16} className="text-brand-600" weight="duotone" />
          <h2 className="font-semibold text-ink-900">Suscripciones ({subscriptions?.length ?? 0})</h2>
        </div>
        {!subscriptions?.length ? (
          <p className="text-sm text-ink-400">Sin suscripciones</p>
        ) : (
          <div className="overflow-x-auto -mx-5 sm:-mx-6 px-5 sm:px-6">
            <table className="w-full text-sm min-w-[500px]">
              <thead>
                <tr className="border-b border-surface-border">
                  <th className="text-left pb-2 text-xs font-semibold text-ink-400">Plan</th>
                  <th className="text-left pb-2 text-xs font-semibold text-ink-400">Estado</th>
                  <th className="text-left pb-2 text-xs font-semibold text-ink-400">Monto</th>
                  <th className="text-left pb-2 text-xs font-semibold text-ink-400">Inicio</th>
                  <th className="text-left pb-2 text-xs font-semibold text-ink-400">Fin</th>
                </tr>
              </thead>
              <tbody>
                {subscriptions.map((s) => (
                  <tr key={s.id} className="border-b border-surface-border last:border-0">
                    <td className="py-2.5">
                      <Badge color={getBadgeColor(s.plan) || "gray"}>{s.plan}</Badge>
                    </td>
                    <td className="py-2.5">
                      <Badge
                        color={
                          s.status === "active" ? "green" : s.status === "cancelled" ? "red" : "gray"
                        }
                      >
                        {s.status}
                      </Badge>
                    </td>
                    <td className="py-2.5 text-ink-700">{money(s.amount)}</td>
                    <td className="py-2.5 text-ink-400 text-xs">{date(s.starts_at)}</td>
                    <td className="py-2.5 text-ink-400 text-xs">{date(s.ends_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Payments */}
      <Card className="p-5 sm:p-6">
        <div className="flex items-center gap-2 mb-4">
          <CreditCard size={16} className="text-accent-600" weight="duotone" />
          <h2 className="font-semibold text-ink-900">Pagos ({payments?.length ?? 0})</h2>
        </div>
        {!payments?.length ? (
          <p className="text-sm text-ink-400">Sin pagos registrados</p>
        ) : (
          <div className="overflow-x-auto -mx-5 sm:-mx-6 px-5 sm:px-6">
            <table className="w-full text-sm min-w-[550px]">
              <thead>
                <tr className="border-b border-surface-border">
                  <th className="text-left pb-2 text-xs font-semibold text-ink-400">ID</th>
                  <th className="text-left pb-2 text-xs font-semibold text-ink-400">Monto</th>
                  <th className="text-left pb-2 text-xs font-semibold text-ink-400">Estado</th>
                  <th className="text-left pb-2 text-xs font-semibold text-ink-400">Plan</th>
                  <th className="text-left pb-2 text-xs font-semibold text-ink-400">Ref</th>
                  <th className="text-left pb-2 text-xs font-semibold text-ink-400">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((p) => (
                  <tr key={p.id} className="border-b border-surface-border last:border-0">
                    <td className="py-2.5 text-ink-400 font-mono text-xs">#{p.id}</td>
                    <td className="py-2.5 font-semibold text-ink-900">{money(p.amount)}</td>
                    <td className="py-2.5">
                      <Badge color={STATUS_COLORS[p.status] || "gray"}>{p.status}</Badge>
                    </td>
                    <td className="py-2.5 text-ink-400 text-xs">{p.plan || "—"}</td>
                    <td className="py-2.5 text-ink-400 font-mono text-xs truncate max-w-[100px]">
                      {p.reference || "—"}
                    </td>
                    <td className="py-2.5 text-ink-400 text-xs">{date(p.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Activity */}
      <Card className="p-5 sm:p-6">
        <div className="flex items-center gap-2 mb-4">
          <ChartLine size={16} className="text-purple-500" weight="duotone" />
          <h2 className="font-semibold text-ink-900">
            Actividad reciente ({activity?.length ?? 0})
          </h2>
        </div>
        {!activity?.length ? (
          <p className="text-sm text-ink-400">Sin actividad registrada</p>
        ) : (
          <div className="space-y-0">
            {activity.map((a, i) => (
              <div
                key={i}
                className="flex items-center justify-between text-sm py-2.5 border-b border-surface-border last:border-0"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="px-2 py-0.5 bg-surface-hover rounded-lg text-xs font-mono flex-shrink-0 text-ink-600">
                    {a.action}
                  </span>
                  {a.resource && (
                    <span className="text-ink-400 text-xs truncate hidden sm:block">
                      {a.resource}
                      {a.resource_id ? ` #${a.resource_id}` : ""}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs text-ink-400 flex-shrink-0">
                  {a.ip && <span className="hidden sm:block">{a.ip}</span>}
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
