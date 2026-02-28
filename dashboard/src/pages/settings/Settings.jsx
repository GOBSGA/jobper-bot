import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import Card, { CardHeader } from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import { useToast } from "../../components/ui/Toast";
import { date } from "../../lib/format";
import { getPlanColor } from "../../lib/planConfig";
import {
  FloppyDisk,
  Bell,
  Buildings,
  MapPin,
  CurrencyDollar,
  Tag,
  User,
  Lock,
  Eye,
  EyeSlash,
  Lightning,
  Trash,
  EnvelopeSimple,
  TelegramLogo,
  Export,
} from "@phosphor-icons/react";

const SECTORS = [
  { key: "tecnologia", label: "Tecnología" },
  { key: "construccion", label: "Construcción" },
  { key: "salud", label: "Salud" },
  { key: "educacion", label: "Educación" },
  { key: "consultoria", label: "Consultoría" },
  { key: "logistica", label: "Logística" },
  { key: "marketing", label: "Marketing" },
  { key: "energia", label: "Energía" },
  { key: "juridico", label: "Jurídico" },
  { key: "ambiental", label: "Ambiental" },
  { key: "agricultura", label: "Agricultura" },
  { key: "mineria", label: "Minería" },
];

const CITIES = [
  "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
  "Bucaramanga", "Pereira", "Santa Marta", "Manizales", "Cúcuta",
  "Ibagué", "Villavicencio", "Pasto", "Montería", "Neiva",
  "Armenia", "Sincelejo", "Popayán", "Valledupar", "Riohacha",
];

const BUDGET_RANGES = [
  { min: 0, max: 50_000_000, label: "Hasta $50M" },
  { min: 50_000_000, max: 200_000_000, label: "$50M – $200M" },
  { min: 200_000_000, max: 500_000_000, label: "$200M – $500M" },
  { min: 500_000_000, max: 2_000_000_000, label: "$500M – $2.000M" },
  { min: 2_000_000_000, max: null, label: "Más de $2.000M" },
];

const SELECT_CLS =
  "w-full px-3 py-2 border border-surface-border rounded-xl text-sm text-ink-700 bg-white focus:outline-none focus:border-brand-500";

function Toggle({ enabled, onToggle, disabled = false }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
        enabled ? "bg-brand-600" : "bg-surface-border"
      } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
          enabled ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

export default function Settings() {
  const { user, refresh, subscription } = useAuth();
  const [form, setForm] = useState({
    company_name: "",
    sector: "",
    keywords: "",
    city: "",
    budget_min: "",
    budget_max: "",
    telegram_chat_id: "",
    daily_digest_enabled: true,
  });
  const [saving, setSaving] = useState(false);
  const [savingNotif, setSavingNotif] = useState(false);
  const [pushEnabled, setPushEnabled] = useState(false);
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "" });
  const [showPw, setShowPw] = useState(false);
  const [savingPw, setSavingPw] = useState(false);
  const toast = useToast();

  const plan = user?.plan || "free";
  const isPaid = !["free", "trial"].includes(plan);

  useEffect(() => {
    if (user) {
      setForm({
        company_name: user.company_name || "",
        sector: user.sector || "",
        keywords: (user.keywords || []).join(", "),
        city: user.city || "",
        budget_min: user.budget_min || "",
        budget_max: user.budget_max || "",
        telegram_chat_id: user.telegram_chat_id || "",
        daily_digest_enabled: user.daily_digest_enabled !== false,
      });
    }
  }, [user]);

  const save = async (e) => {
    if (e?.preventDefault) e.preventDefault();
    setSaving(true);
    try {
      await api.put("/user/profile", {
        company_name: form.company_name,
        sector: form.sector,
        keywords: form.keywords.split(",").map((k) => k.trim()).filter(Boolean),
        city: form.city,
        budget_min: form.budget_min ? Number(form.budget_min) : null,
        budget_max: form.budget_max ? Number(form.budget_max) : null,
      });
      await refresh();
      toast.success("Perfil guardado");
    } catch (err) {
      toast.error(err.error || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const saveNotifications = async () => {
    setSavingNotif(true);
    try {
      await api.put("/user/profile", {
        telegram_chat_id: form.telegram_chat_id || null,
        daily_digest_enabled: form.daily_digest_enabled,
      });
      await refresh();
      toast.success("Notificaciones guardadas");
    } catch (err) {
      toast.error(err.error || "Error al guardar");
    } finally {
      setSavingNotif(false);
    }
  };

  const changePassword = async (e) => {
    e.preventDefault();
    if (pwForm.next.length < 6) { toast.error("Mínimo 6 caracteres"); return; }
    if (pwForm.next !== pwForm.confirm) { toast.error("Las contraseñas no coinciden"); return; }
    setSavingPw(true);
    try {
      await api.post("/user/change-password", {
        current_password: pwForm.current,
        new_password: pwForm.next,
      });
      setPwForm({ current: "", next: "", confirm: "" });
      toast.success("Contraseña actualizada");
    } catch (err) {
      toast.error(err.error || "Error al cambiar la contraseña");
    } finally {
      setSavingPw(false);
    }
  };

  const enablePush = async () => {
    try {
      const reg = await navigator.serviceWorker?.ready;
      if (!reg) { toast.error("Servicio no disponible en este navegador"); return; }
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: import.meta.env.VITE_VAPID_PUBLIC_KEY,
      });
      await api.post("/user/push-subscription", sub.toJSON());
      setPushEnabled(true);
      toast.success("Notificaciones push activadas");
    } catch {
      toast.error("No se pudo activar las notificaciones push.");
    }
  };

  return (
    <div className="space-y-5 pb-8">
      <h1 className="text-xl sm:text-2xl font-bold text-ink-900">Configuración</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* ── Left column ── */}
        <div className="space-y-5">
          {/* PLAN */}
          <Card>
            <CardHeader title="Plan y facturación" />
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 rounded-xl bg-surface-hover border border-surface-border">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase ${getPlanColor(plan, "badge")}`}>
                      {plan}
                    </span>
                    {isPaid && subscription?.expires_at && (
                      <span className="text-xs text-ink-400">· Vence: {date(subscription.expires_at)}</span>
                    )}
                  </div>
                  {subscription?.days_remaining != null && isPaid && (
                    <p className="text-xs text-ink-400 mt-1">{subscription.days_remaining} días restantes</p>
                  )}
                  {!isPaid && (
                    <p className="text-xs text-ink-400 mt-1">Plan gratuito — funcionalidad limitada</p>
                  )}
                </div>
                <Link to="/payments">
                  <Button size="sm" variant={isPaid ? "secondary" : "primary"}>
                    <Lightning size={14} weight="duotone" />
                    {isPaid ? "Cambiar" : "Mejorar"}
                  </Button>
                </Link>
              </div>
              <Link to="/referrals" className="text-sm text-brand-600 hover:text-brand-700 font-medium transition block">
                Referir amigos y obtener descuentos →
              </Link>
            </div>
          </Card>

          {/* PERFIL */}
          <Card>
            <CardHeader title="Tu perfil" />
            <form onSubmit={save} className="space-y-4">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-ink-700 mb-1.5">
                  <User size={15} className="text-ink-400" /> Email
                </label>
                <Input value={user?.email || ""} disabled className="bg-surface-hover" />
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-ink-700 mb-1.5">
                  <Buildings size={15} className="text-ink-400" /> Nombre o empresa
                </label>
                <Input
                  value={form.company_name}
                  onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                  placeholder="Tu nombre, empresa o razón social"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-ink-700 mb-1.5">
                    <Tag size={15} className="text-ink-400" /> Sector
                  </label>
                  <select
                    value={form.sector}
                    onChange={(e) => setForm({ ...form, sector: e.target.value })}
                    className={SELECT_CLS}
                  >
                    <option value="">Seleccionar...</option>
                    {SECTORS.map((s) => (
                      <option key={s.key} value={s.key}>{s.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-ink-700 mb-1.5">
                    <MapPin size={15} className="text-ink-400" /> Ciudad
                  </label>
                  <select
                    value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                    className={SELECT_CLS}
                  >
                    <option value="">Seleccionar...</option>
                    {CITIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-ink-700 mb-1.5">
                  <Tag size={15} className="text-ink-400" /> Palabras clave
                </label>
                <Input
                  value={form.keywords}
                  onChange={(e) => setForm({ ...form, keywords: e.target.value })}
                  placeholder="software, desarrollo, cloud, IA"
                />
                <p className="text-xs text-ink-400 mt-1">Separadas por coma. Se usan para encontrar contratos relevantes.</p>
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-ink-700 mb-2">
                  <CurrencyDollar size={15} className="text-ink-400" /> Presupuesto objetivo
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {BUDGET_RANGES.map((r, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setForm({ ...form, budget_min: r.min || "", budget_max: r.max || "" })}
                      className={`px-3 py-2 rounded-xl border text-sm font-medium transition-all ${
                        form.budget_min == r.min && form.budget_max == r.max
                          ? "border-brand-500 bg-brand-50 text-brand-700"
                          : "border-surface-border hover:bg-surface-hover text-ink-600"
                      }`}
                    >
                      {r.label}
                    </button>
                  ))}
                </div>
              </div>

              <Button type="submit" disabled={saving} className="w-full sm:w-auto">
                <FloppyDisk size={15} /> {saving ? "Guardando..." : "Guardar perfil"}
              </Button>
            </form>
          </Card>
        </div>

        {/* ── Right column ── */}
        <div className="space-y-5">
          {/* NOTIFICACIONES */}
          <Card>
            <CardHeader title="Notificaciones" />
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-ink-900 flex items-center gap-1.5">
                    <Bell size={15} className="text-ink-400" /> Push en el navegador
                  </p>
                  <p className="text-xs text-ink-400 mt-0.5">Alertas cuando aparecen contratos relevantes.</p>
                </div>
                <Button variant="secondary" size="sm" onClick={enablePush} disabled={pushEnabled}>
                  {pushEnabled ? "Activado" : "Activar"}
                </Button>
              </div>

              <div className="border-t border-surface-border pt-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-ink-900 flex items-center gap-1.5">
                    <EnvelopeSimple size={15} className="text-ink-400" /> Resumen diario por email
                  </p>
                  <p className="text-xs text-ink-400 mt-0.5">
                    Los mejores contratos del día, cada mañana.
                    {!isPaid && <span className="text-amber-600 font-medium"> Requiere plan Cazador.</span>}
                  </p>
                </div>
                <Toggle
                  enabled={form.daily_digest_enabled && isPaid}
                  onToggle={() => isPaid && setForm({ ...form, daily_digest_enabled: !form.daily_digest_enabled })}
                  disabled={!isPaid}
                />
              </div>

              <div className="border-t border-surface-border pt-4">
                <p className="text-sm font-medium text-ink-900 flex items-center gap-1.5 mb-1">
                  <TelegramLogo size={15} weight="duotone" className="text-brand-500" /> Telegram
                </p>
                <p className="text-xs text-ink-400 mb-2">
                  Busca <span className="font-mono bg-surface-hover px-1 rounded text-ink-600">@JobperAlertas_bot</span> y
                  escribe <span className="font-mono bg-surface-hover px-1 rounded text-ink-600">/start</span> para obtener tu Chat ID.
                </p>
                <Input
                  placeholder="Chat ID de Telegram (ej: 123456789)"
                  value={form.telegram_chat_id}
                  onChange={(e) => setForm({ ...form, telegram_chat_id: e.target.value })}
                />
              </div>

              <Button onClick={saveNotifications} disabled={savingNotif} size="sm" variant="secondary">
                <FloppyDisk size={14} /> {savingNotif ? "Guardando..." : "Guardar notificaciones"}
              </Button>
            </div>
          </Card>

          {/* SEGURIDAD */}
          <Card>
            <CardHeader title="Seguridad" />
            <form onSubmit={changePassword} className="space-y-4">
              <p className="text-xs text-ink-400">
                Si accedes con Magic Link (sin contraseña), deja el campo actual en blanco.
              </p>
              <Input
                label="Contraseña actual"
                type={showPw ? "text" : "password"}
                placeholder="Dejar en blanco si usas Magic Link"
                value={pwForm.current}
                onChange={(e) => setPwForm({ ...pwForm, current: e.target.value })}
              />
              <Input
                label="Nueva contraseña"
                type={showPw ? "text" : "password"}
                placeholder="Mínimo 6 caracteres"
                value={pwForm.next}
                onChange={(e) => setPwForm({ ...pwForm, next: e.target.value })}
                required
                minLength={6}
              />
              <Input
                label="Confirmar nueva contraseña"
                type={showPw ? "text" : "password"}
                value={pwForm.confirm}
                onChange={(e) => setPwForm({ ...pwForm, confirm: e.target.value })}
                required
              />
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="flex items-center gap-1.5 text-sm text-ink-400 hover:text-ink-600"
                >
                  {showPw ? <EyeSlash size={15} /> : <Eye size={15} />}
                  {showPw ? "Ocultar" : "Mostrar"}
                </button>
                <Button type="submit" size="sm" disabled={savingPw} className="ml-auto">
                  <Lock size={14} />
                  {savingPw ? "Guardando..." : "Cambiar contraseña"}
                </Button>
              </div>
            </form>
          </Card>

          {/* PRIVACIDAD */}
          <Card>
            <CardHeader title="Privacidad y datos" />
            <div className="space-y-4">
              <div className="flex items-center justify-between py-2">
                <div>
                  <p className="text-sm font-medium text-ink-900">Exportar mis datos</p>
                  <p className="text-xs text-ink-400">Copia de tus favoritos, pipeline y perfil.</p>
                </div>
                <Button variant="secondary" size="sm" onClick={() => {
                  window.open("mailto:soporte@jobper.co?subject=Solicitud%20de%20exportación%20de%20datos", "_blank");
                }}>
                  <Export size={14} /> Solicitar
                </Button>
              </div>

              <div className="border-t border-surface-border pt-4 flex items-center justify-between py-2">
                <div>
                  <p className="text-sm font-medium text-ink-900">Política de privacidad</p>
                  <p className="text-xs text-ink-400">Cómo usamos y protegemos tus datos.</p>
                </div>
                <a href="/privacy" target="_blank" className="text-sm text-brand-600 hover:underline font-medium">
                  Ver →
                </a>
              </div>

              <div className="border-t border-surface-border pt-4">
                <div className="p-4 bg-red-50 rounded-xl border border-red-100">
                  <p className="text-sm font-semibold text-red-700 flex items-center gap-1.5 mb-1">
                    <Trash size={14} /> Eliminar cuenta
                  </p>
                  <p className="text-xs text-red-600 mb-3">
                    Irreversible. Elimina todos tus datos, favoritos, pipeline y suscripción activa.
                  </p>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="border-red-200 text-red-600 hover:bg-red-100"
                    onClick={async () => {
                      const confirmed = window.confirm(
                        `¿Eliminar permanentemente la cuenta de ${user?.email}?\n\nSe borrarán todos tus datos. Esta acción es IRREVERSIBLE.`
                      );
                      if (!confirmed) return;
                      const reconfirmed = window.confirm("Última confirmación: ¿seguro que quieres eliminar tu cuenta?");
                      if (!reconfirmed) return;
                      try {
                        await api.del("/user/account");
                        window.location.href = "/";
                      } catch (err) {
                        toast.error(err.error || "Error eliminando cuenta. Escríbenos a soporte@jobper.co");
                      }
                    }}
                  >
                    <Trash size={14} /> Eliminar permanentemente
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
