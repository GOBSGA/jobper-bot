import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import { useToast } from "../../components/ui/Toast";
import { date } from "../../lib/format";
import { getPlanColor } from "../../lib/planConfig";
import {
  FloppyDisk, Bell, Buildings, MapPin, CurrencyDollar, Tag,
  User, Lock, Eye, EyeSlash, Lightning, Trash, EnvelopeSimple,
  TelegramLogo, Export, Shield, Phone, WhatsappLogo,
  SlidersHorizontal, Star, Gift,
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

const NAV = [
  { key: "empresa",         label: "Mi empresa",      icon: Buildings,        desc: "Nombre, sector y contacto" },
  { key: "preferencias",   label: "Preferencias",     icon: SlidersHorizontal, desc: "Keywords y presupuesto" },
  { key: "notificaciones", label: "Notificaciones",   icon: Bell,             desc: "Email, push y Telegram" },
  { key: "plan",           label: "Plan",             icon: Lightning,        desc: "Suscripción y referidos" },
  { key: "seguridad",      label: "Seguridad",        icon: Shield,           desc: "Contraseña y datos" },
];

const SELECT_CLS =
  "w-full px-3 py-2 border border-surface-border rounded-xl text-sm text-ink-700 bg-white focus:outline-none focus:border-brand-500 transition-colors";

function SectionTitle({ icon: Icon, title, desc }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2.5 mb-1">
        <div className="w-8 h-8 rounded-xl bg-brand-50 flex items-center justify-center flex-shrink-0">
          <Icon size={16} className="text-brand-600" weight="duotone" />
        </div>
        <h2 className="text-base font-bold text-ink-900">{title}</h2>
      </div>
      {desc && <p className="text-sm text-ink-400 ml-10">{desc}</p>}
    </div>
  );
}

function FieldLabel({ children }) {
  return <label className="block text-xs font-semibold text-ink-600 mb-1.5 uppercase tracking-wide">{children}</label>;
}

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
      <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
        enabled ? "translate-x-6" : "translate-x-1"
      }`} />
    </button>
  );
}

function NotifRow({ icon: Icon, iconClass = "text-ink-400", title, desc, action }) {
  return (
    <div className="flex items-center justify-between py-4 border-b border-surface-border last:border-0">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-xl bg-surface-hover flex items-center justify-center flex-shrink-0 mt-0.5">
          <Icon size={15} className={iconClass} weight="duotone" />
        </div>
        <div>
          <p className="text-sm font-medium text-ink-900">{title}</p>
          <p className="text-xs text-ink-400 mt-0.5">{desc}</p>
        </div>
      </div>
      <div className="flex-shrink-0 ml-4">{action}</div>
    </div>
  );
}

export default function Settings() {
  const { user, refresh, subscription } = useAuth();
  const [tab, setTab] = useState("empresa");
  const [form, setForm] = useState({
    company_name: "",
    sector: "",
    keywords: "",
    city: "",
    budget_min: "",
    budget_max: "",
    phone: "",
    whatsapp_number: "",
    whatsapp_enabled: false,
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
        phone: user.phone || "",
        whatsapp_number: user.whatsapp_number || "",
        whatsapp_enabled: user.whatsapp_enabled || false,
        telegram_chat_id: user.telegram_chat_id || "",
        daily_digest_enabled: user.daily_digest_enabled !== false,
      });
    }
  }, [user]);

  const saveEmpresa = async (e) => {
    e?.preventDefault();
    setSaving(true);
    try {
      await api.put("/user/profile", {
        company_name: form.company_name,
        sector: form.sector,
        city: form.city,
        phone: form.phone || null,
      });
      await refresh();
      toast.success("Empresa guardada");
    } catch (err) {
      toast.error(err.error || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const savePreferencias = async (e) => {
    e?.preventDefault();
    setSaving(true);
    try {
      await api.put("/user/profile", {
        keywords: form.keywords.split(",").map((k) => k.trim()).filter(Boolean),
        budget_min: form.budget_min ? Number(form.budget_min) : null,
        budget_max: form.budget_max ? Number(form.budget_max) : null,
      });
      await refresh();
      toast.success("Preferencias guardadas");
    } catch (err) {
      toast.error(err.error || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const saveNotif = async () => {
    setSavingNotif(true);
    try {
      await api.put("/user/profile", {
        telegram_chat_id: form.telegram_chat_id || null,
        daily_digest_enabled: form.daily_digest_enabled,
        whatsapp_number: form.whatsapp_number || null,
        whatsapp_enabled: form.whatsapp_enabled,
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

  const activeNav = NAV.find((n) => n.key === tab);

  return (
    <div className="flex gap-0 h-full min-h-screen -mt-1">

      {/* ── Sidebar navigation ── */}
      <aside className="hidden lg:flex flex-col w-56 flex-shrink-0 border-r border-surface-border bg-white pr-0 py-2 mr-8">
        <p className="text-[10px] font-bold tracking-widest uppercase text-ink-300 px-3 mb-3 mt-1">Configuración</p>
        {NAV.map(({ key, label, icon: Icon, desc }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all mb-0.5 ${
              tab === key
                ? "bg-brand-50 text-brand-700"
                : "text-ink-600 hover:bg-surface-hover hover:text-ink-900"
            }`}
          >
            <Icon size={17} weight={tab === key ? "duotone" : "regular"} className={tab === key ? "text-brand-600" : "text-ink-400"} />
            <span className="text-sm font-medium">{label}</span>
          </button>
        ))}
      </aside>

      {/* ── Mobile: horizontal tabs ── */}
      <div className="lg:hidden w-full">
        <div className="flex gap-0.5 overflow-x-auto border-b border-surface-border mb-5 pb-0 -mx-4 px-4">
          {NAV.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap ${
                tab === key ? "border-brand-600 text-brand-700" : "border-transparent text-ink-500"
              }`}
            >
              <Icon size={14} /> {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Content area ── */}
      <main className="flex-1 min-w-0 pb-16 max-w-3xl">

        {/* Page title — desktop only */}
        <div className="hidden lg:flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-ink-900">{activeNav?.label}</h1>
            <p className="text-sm text-ink-400 mt-0.5">{activeNav?.desc}</p>
          </div>
        </div>

        {/* ── EMPRESA ── */}
        {tab === "empresa" && (
          <form onSubmit={saveEmpresa} className="space-y-6">
            {/* Avatar + email row */}
            <div className="bg-white rounded-2xl border border-surface-border p-6">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 rounded-2xl bg-brand-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl font-bold text-brand-700">
                    {(user?.company_name || user?.email || "?")[0].toUpperCase()}
                  </span>
                </div>
                <div className="min-w-0">
                  <p className="font-bold text-ink-900 text-base">{user?.company_name || user?.email}</p>
                  <p className="text-sm text-ink-400">{user?.email}</p>
                  <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-bold uppercase ${getPlanColor(plan, "badge")}`}>
                    {plan}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <FieldLabel>Email</FieldLabel>
                  <div className="relative">
                    <EnvelopeSimple size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-300" />
                    <input
                      value={user?.email || ""}
                      disabled
                      className="w-full pl-9 pr-3 py-2 border border-surface-border rounded-xl text-sm text-ink-400 bg-surface-hover cursor-not-allowed"
                    />
                  </div>
                </div>

                <div className="md:col-span-2">
                  <FieldLabel>Nombre o empresa</FieldLabel>
                  <div className="relative">
                    <Buildings size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-300" />
                    <input
                      value={form.company_name}
                      onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                      placeholder="Tu nombre, empresa o razón social"
                      className="w-full pl-9 pr-3 py-2 border border-surface-border rounded-xl text-sm text-ink-900 focus:border-brand-400 focus:ring-2 focus:ring-brand-100 outline-none transition-all"
                    />
                  </div>
                </div>

                <div>
                  <FieldLabel>Sector</FieldLabel>
                  <select value={form.sector} onChange={(e) => setForm({ ...form, sector: e.target.value })} className={SELECT_CLS}>
                    <option value="">Seleccionar...</option>
                    {SECTORS.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
                  </select>
                </div>

                <div>
                  <FieldLabel>Ciudad</FieldLabel>
                  <select value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className={SELECT_CLS}>
                    <option value="">Seleccionar...</option>
                    {CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>

                <div>
                  <FieldLabel>Teléfono</FieldLabel>
                  <div className="relative">
                    <Phone size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-300" />
                    <input
                      value={form.phone}
                      onChange={(e) => setForm({ ...form, phone: e.target.value })}
                      placeholder="+57 300 000 0000"
                      className="w-full pl-9 pr-3 py-2 border border-surface-border rounded-xl text-sm text-ink-900 focus:border-brand-400 focus:ring-2 focus:ring-brand-100 outline-none transition-all"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button type="submit" disabled={saving}>
                <FloppyDisk size={15} weight="duotone" /> {saving ? "Guardando..." : "Guardar empresa"}
              </Button>
            </div>
          </form>
        )}

        {/* ── PREFERENCIAS ── */}
        {tab === "preferencias" && (
          <form onSubmit={savePreferencias} className="space-y-6">
            <div className="bg-white rounded-2xl border border-surface-border p-6 space-y-6">

              {/* Keywords */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <FieldLabel>Palabras clave de búsqueda</FieldLabel>
                  <span className="text-xs text-ink-400">{form.keywords.split(",").filter(k => k.trim()).length} keywords</span>
                </div>
                <div className="relative">
                  <Tag size={15} className="absolute left-3 top-3 text-ink-300" />
                  <textarea
                    value={form.keywords}
                    onChange={(e) => setForm({ ...form, keywords: e.target.value })}
                    placeholder="software, desarrollo web, cloud, inteligencia artificial, ciberseguridad..."
                    rows={3}
                    className="w-full pl-9 pr-3 py-2.5 border border-surface-border rounded-xl text-sm text-ink-900 focus:border-brand-400 focus:ring-2 focus:ring-brand-100 outline-none resize-none transition-all"
                  />
                </div>
                <p className="text-xs text-ink-400 mt-1.5">
                  Separadas por coma. Jobper usa estas palabras para encontrar y ranquear contratos relevantes para ti.
                </p>

                {/* Live preview of keywords as chips */}
                {form.keywords && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {form.keywords.split(",").map(k => k.trim()).filter(Boolean).map((kw, i) => (
                      <span key={i} className="text-xs px-2.5 py-1 rounded-full bg-brand-50 text-brand-700 border border-brand-100 font-medium">
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="border-t border-surface-border" />

              {/* Budget range */}
              <div>
                <FieldLabel>Presupuesto objetivo de contratos</FieldLabel>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
                  {BUDGET_RANGES.map((r, i) => {
                    const isActive = form.budget_min == r.min && form.budget_max == r.max;
                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => setForm({ ...form, budget_min: r.min || "", budget_max: r.max || "" })}
                        className={`px-3 py-2.5 rounded-xl border text-sm font-medium transition-all text-left ${
                          isActive
                            ? "border-brand-500 bg-brand-50 text-brand-700 shadow-sm"
                            : "border-surface-border hover:bg-surface-hover text-ink-600"
                        }`}
                      >
                        {r.label}
                      </button>
                    );
                  })}
                </div>
                <p className="text-xs text-ink-400 mt-2">Filtra la sección "Para ti" para mostrar contratos dentro de tu rango de interés.</p>
              </div>
            </div>

            <div className="flex justify-end">
              <Button type="submit" disabled={saving}>
                <FloppyDisk size={15} weight="duotone" /> {saving ? "Guardando..." : "Guardar preferencias"}
              </Button>
            </div>
          </form>
        )}

        {/* ── NOTIFICACIONES ── */}
        {tab === "notificaciones" && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-surface-border p-6">
              <NotifRow
                icon={Bell}
                iconClass="text-brand-500"
                title="Notificaciones push en el navegador"
                desc="Alertas instantáneas cuando aparecen contratos relevantes para ti."
                action={
                  <Button variant="secondary" size="sm" onClick={enablePush} disabled={pushEnabled}>
                    {pushEnabled ? "✓ Activado" : "Activar"}
                  </Button>
                }
              />

              <NotifRow
                icon={EnvelopeSimple}
                iconClass="text-blue-500"
                title="Resumen diario por email"
                desc={
                  <>
                    Los mejores contratos del día, cada mañana a las 7am.
                    {!isPaid && <span className="text-amber-600 font-semibold"> Requiere plan Cazador o superior.</span>}
                  </>
                }
                action={
                  <Toggle
                    enabled={form.daily_digest_enabled && isPaid}
                    onToggle={() => isPaid && setForm({ ...form, daily_digest_enabled: !form.daily_digest_enabled })}
                    disabled={!isPaid}
                  />
                }
              />

              <NotifRow
                icon={WhatsappLogo}
                iconClass="text-green-500"
                title="WhatsApp"
                desc="Recibe alertas de nuevos contratos por WhatsApp."
                action={
                  <Toggle
                    enabled={form.whatsapp_enabled}
                    onToggle={() => setForm({ ...form, whatsapp_enabled: !form.whatsapp_enabled })}
                  />
                }
              />

              {form.whatsapp_enabled && (
                <div className="ml-11 -mt-2 mb-4">
                  <div className="relative">
                    <WhatsappLogo size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-green-500" />
                    <input
                      value={form.whatsapp_number}
                      onChange={(e) => setForm({ ...form, whatsapp_number: e.target.value })}
                      placeholder="+57 300 000 0000"
                      className="w-full pl-9 pr-3 py-2 border border-surface-border rounded-xl text-sm focus:border-brand-400 outline-none transition-all"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Telegram */}
            <div className="bg-white rounded-2xl border border-surface-border p-6">
              <div className="flex items-start gap-3 mb-4">
                <div className="w-8 h-8 rounded-xl bg-surface-hover flex items-center justify-center flex-shrink-0">
                  <TelegramLogo size={16} weight="duotone" className="text-brand-500" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-ink-900">Telegram</p>
                  <p className="text-xs text-ink-400 mt-0.5">
                    Busca <span className="font-mono bg-surface-hover px-1.5 py-0.5 rounded text-ink-700 text-[11px]">@JobperAlertas_bot</span> y
                    escribe <span className="font-mono bg-surface-hover px-1.5 py-0.5 rounded text-ink-700 text-[11px]">/start</span> para obtener tu Chat ID.
                  </p>
                </div>
              </div>
              <div className="relative ml-11">
                <TelegramLogo size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-300" />
                <input
                  placeholder="Chat ID (ej: 123456789)"
                  value={form.telegram_chat_id}
                  onChange={(e) => setForm({ ...form, telegram_chat_id: e.target.value })}
                  className="w-full pl-9 pr-3 py-2 border border-surface-border rounded-xl text-sm focus:border-brand-400 outline-none transition-all"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={saveNotif} disabled={savingNotif}>
                <FloppyDisk size={15} weight="duotone" /> {savingNotif ? "Guardando..." : "Guardar notificaciones"}
              </Button>
            </div>
          </div>
        )}

        {/* ── PLAN ── */}
        {tab === "plan" && (
          <div className="space-y-5">
            {/* Current plan card */}
            <div className="bg-white rounded-2xl border border-surface-border p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-widest text-ink-400 mb-2">Plan actual</p>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold uppercase ${getPlanColor(plan, "badge")}`}>
                      {plan}
                    </span>
                    {isPaid && subscription?.expires_at && (
                      <span className="text-sm text-ink-400">· Vence {date(subscription.expires_at)}</span>
                    )}
                  </div>
                  {subscription?.days_remaining != null && isPaid ? (
                    <div className="space-y-1.5">
                      <p className="text-sm text-ink-500">{subscription.days_remaining} días restantes</p>
                      <div className="w-48 h-1.5 bg-surface-border rounded-full overflow-hidden">
                        <div
                          className="h-full bg-brand-500 rounded-full"
                          style={{ width: `${Math.min((subscription.days_remaining / 30) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-ink-400">Explora los planes disponibles para desbloquear todas las funciones.</p>
                  )}
                </div>
                <Link to="/payments">
                  <Button variant={isPaid ? "secondary" : "primary"}>
                    <Lightning size={15} weight="duotone" />
                    {isPaid ? "Cambiar plan" : "Mejorar plan"}
                  </Button>
                </Link>
              </div>
            </div>

            {/* Referrals */}
            <div className="bg-white rounded-2xl border border-surface-border p-6">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-2xl bg-amber-50 flex items-center justify-center flex-shrink-0">
                  <Gift size={20} weight="duotone" className="text-amber-500" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-ink-900 mb-1">Programa de referidos</p>
                  <p className="text-sm text-ink-400 mb-3">Invita a otras empresas y obtén descuentos en tu próxima renovación. Por cada referido activo, ganas 10% de descuento.</p>
                  <Link to="/referrals">
                    <Button variant="secondary" size="sm">
                      <Gift size={14} weight="duotone" /> Ver mis referidos →
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── SEGURIDAD ── */}
        {tab === "seguridad" && (
          <div className="space-y-5">
            {/* Password */}
            <div className="bg-white rounded-2xl border border-surface-border p-6">
              <div className="flex items-center gap-2.5 mb-5">
                <div className="w-8 h-8 rounded-xl bg-surface-hover flex items-center justify-center">
                  <Lock size={15} className="text-ink-500" weight="duotone" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-ink-900">Cambiar contraseña</p>
                  <p className="text-xs text-ink-400">Si accedes con Magic Link, deja el campo actual en blanco.</p>
                </div>
              </div>
              <form onSubmit={changePassword} className="space-y-3">
                <Input
                  label="Contraseña actual"
                  type={showPw ? "text" : "password"}
                  placeholder="Dejar en blanco si usas Magic Link"
                  value={pwForm.current}
                  onChange={(e) => setPwForm({ ...pwForm, current: e.target.value })}
                />
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Nueva contraseña"
                    type={showPw ? "text" : "password"}
                    placeholder="Mínimo 6 caracteres"
                    value={pwForm.next}
                    onChange={(e) => setPwForm({ ...pwForm, next: e.target.value })}
                    required minLength={6}
                  />
                  <Input
                    label="Confirmar contraseña"
                    type={showPw ? "text" : "password"}
                    value={pwForm.confirm}
                    onChange={(e) => setPwForm({ ...pwForm, confirm: e.target.value })}
                    required
                  />
                </div>
                <div className="flex items-center gap-3 pt-1">
                  <button type="button" onClick={() => setShowPw(!showPw)}
                    className="flex items-center gap-1.5 text-sm text-ink-400 hover:text-ink-600">
                    {showPw ? <EyeSlash size={14} /> : <Eye size={14} />}
                    {showPw ? "Ocultar" : "Mostrar"}
                  </button>
                  <Button type="submit" size="sm" disabled={savingPw} className="ml-auto">
                    <Lock size={13} /> {savingPw ? "Guardando..." : "Cambiar contraseña"}
                  </Button>
                </div>
              </form>
            </div>

            {/* Privacy */}
            <div className="bg-white rounded-2xl border border-surface-border p-6 space-y-4">
              <p className="text-sm font-semibold text-ink-900">Privacidad y datos</p>

              <div className="flex items-center justify-between py-3 border-b border-surface-border">
                <div>
                  <p className="text-sm font-medium text-ink-900">Exportar mis datos</p>
                  <p className="text-xs text-ink-400">Copia de tus favoritos, pipeline y perfil en JSON.</p>
                </div>
                <Button variant="secondary" size="sm" onClick={() =>
                  window.open("mailto:soporte@jobper.co?subject=Solicitud%20de%20exportación%20de%20datos", "_blank")
                }>
                  <Export size={13} /> Solicitar
                </Button>
              </div>

              <div className="flex items-center justify-between py-2">
                <div>
                  <p className="text-sm font-medium text-ink-900">Política de privacidad</p>
                  <p className="text-xs text-ink-400">Cómo usamos y protegemos tus datos (Ley 1581/2012).</p>
                </div>
                <a href="/privacy" target="_blank" className="text-sm text-brand-600 hover:underline font-medium">
                  Ver →
                </a>
              </div>
            </div>

            {/* Danger zone */}
            <div className="rounded-2xl border border-red-100 bg-red-50/50 p-6">
              <div className="flex items-center gap-2 mb-2">
                <Trash size={15} className="text-red-500" />
                <p className="text-sm font-semibold text-red-700">Zona de peligro</p>
              </div>
              <p className="text-xs text-red-600 mb-4">
                Eliminar la cuenta es <strong>irreversible</strong>. Se borrarán permanentemente todos tus datos, favoritos, pipeline y suscripción activa.
              </p>
              <Button
                variant="secondary"
                size="sm"
                className="border-red-200 text-red-600 hover:bg-red-100"
                onClick={async () => {
                  const confirmed = window.confirm(`¿Eliminar permanentemente la cuenta de ${user?.email}?\n\nSe borrarán todos tus datos. Esta acción es IRREVERSIBLE.`);
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
                <Trash size={13} /> Eliminar mi cuenta
              </Button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
