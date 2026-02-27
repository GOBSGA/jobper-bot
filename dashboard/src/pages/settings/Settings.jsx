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
  Save, Bell, Building2, MapPin, DollarSign, Tag, User, MessageCircle,
  Lock, Eye, EyeOff, Filter, SlidersHorizontal, Zap, Trash2, Download, Search,
} from "lucide-react";

const SECTORS = [
  { key: "tecnologia", label: "Tecnología", emoji: "💻" },
  { key: "construccion", label: "Construcción", emoji: "🏗️" },
  { key: "salud", label: "Salud", emoji: "🏥" },
  { key: "educacion", label: "Educación", emoji: "📚" },
  { key: "consultoria", label: "Consultoría", emoji: "📊" },
  { key: "logistica", label: "Logística", emoji: "🚚" },
  { key: "marketing", label: "Marketing", emoji: "📢" },
  { key: "energia", label: "Energía", emoji: "⚡" },
  { key: "juridico", label: "Jurídico", emoji: "⚖️" },
  { key: "ambiental", label: "Ambiental", emoji: "🌿" },
  { key: "agricultura", label: "Agricultura", emoji: "🌾" },
  { key: "mineria", label: "Minería", emoji: "⛏️" },
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

const SOURCES = ["SECOP I", "SECOP II", "BID", "Banco Mundial", "Ecopetrol", "EPM", "UNGM"];
const CONTRACT_TYPES = [
  "Servicios profesionales", "Obra pública", "Suministros",
  "Consultoría", "Tecnología", "Capacitación", "Interventoría",
];

export default function Settings() {
  const { user, refresh, subscription } = useAuth();
  const [form, setForm] = useState({
    company_name: "",
    sector: "",
    keywords: "",
    city: "",
    budget_min: "",
    budget_max: "",
    whatsapp_number: "",
    whatsapp_enabled: false,
    telegram_chat_id: "",
  });
  const [saving, setSaving] = useState(false);
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
        whatsapp_number: user.whatsapp_number || "",
        whatsapp_enabled: user.whatsapp_enabled || false,
        telegram_chat_id: user.telegram_chat_id || "",
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
        whatsapp_number: form.whatsapp_number || null,
        whatsapp_enabled: form.whatsapp_enabled,
        telegram_chat_id: form.telegram_chat_id || null,
      });
      await refresh();
      toast.success("Perfil guardado");
    } catch (err) {
      toast.error(err.error || "Error al guardar");
    } finally {
      setSaving(false);
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

  const selectBudgetRange = (range) => {
    setForm({ ...form, budget_min: range.min || "", budget_max: range.max || "" });
  };

  const currentBudgetLabel = () => {
    if (!form.budget_min && !form.budget_max) return null;
    const found = BUDGET_RANGES.find((r) => r.min === form.budget_min && r.max === form.budget_max);
    return found?.label || `$${(form.budget_min / 1_000_000).toFixed(0)}M – ${form.budget_max ? "$" + (form.budget_max / 1_000_000).toFixed(0) + "M" : "∞"}`;
  };

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Configuración</h1>

      {/* ── PLAN & FACTURACIÓN ── */}
      <Card>
        <CardHeader title="Plan y facturación" subtitle="Tu suscripción actual" />
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50 border border-gray-100">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase ${getPlanColor(plan, "badge")}`}>
                  {plan}
                </span>
                {isPaid && subscription?.expires_at && (
                  <span className="text-xs text-gray-500">· Vence: {date(subscription.expires_at)}</span>
                )}
              </div>
              {subscription?.days_remaining != null && isPaid && (
                <p className="text-xs text-gray-400 mt-1">{subscription.days_remaining} días restantes</p>
              )}
              {!isPaid && (
                <p className="text-xs text-gray-400 mt-1">Plan gratuito — funcionalidad limitada</p>
              )}
            </div>
            <Link to="/payments">
              <Button size="sm" variant={isPaid ? "secondary" : "primary"}>
                <Zap className="h-3.5 w-3.5" />
                {isPaid ? "Cambiar plan" : "Mejorar plan"}
              </Button>
            </Link>
          </div>
          <Link to="/referrals" className="text-sm text-brand-600 hover:text-brand-700 font-medium transition block">
            Referir amigos y obtener descuentos →
          </Link>
        </div>
      </Card>

      {/* ── PERFIL ── */}
      <Card>
        <CardHeader title="Tu perfil" subtitle="Personaliza qué contratos te mostramos" />
        <form onSubmit={save} className="space-y-5">
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <User className="h-4 w-4 text-gray-400" /> Email
            </label>
            <Input value={user?.email || ""} disabled className="bg-gray-50" />
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <Building2 className="h-4 w-4 text-gray-400" /> Nombre o empresa
            </label>
            <Input
              value={form.company_name}
              onChange={(e) => setForm({ ...form, company_name: e.target.value })}
              placeholder="Tu nombre, empresa o razón social"
            />
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Tag className="h-4 w-4 text-gray-400" /> Sector
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {SECTORS.map((s) => (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => setForm({ ...form, sector: s.key })}
                  className={`px-3 py-2 rounded-lg border text-sm font-medium transition-all ${
                    form.sector === s.key
                      ? "border-brand-500 bg-brand-50 text-brand-700"
                      : "border-gray-200 hover:border-gray-300 text-gray-600"
                  }`}
                >
                  <span className="mr-1">{s.emoji}</span> {s.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <Tag className="h-4 w-4 text-gray-400" /> Palabras clave
            </label>
            <Input
              value={form.keywords}
              onChange={(e) => setForm({ ...form, keywords: e.target.value })}
              placeholder="software, desarrollo, cloud, IA"
            />
            <p className="text-xs text-gray-500 mt-1">Separadas por coma. El motor de match las usa para encontrar tus contratos.</p>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <MapPin className="h-4 w-4 text-gray-400" /> Ciudad principal
            </label>
            <div className="flex flex-wrap gap-2">
              {CITIES.slice(0, 10).map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setForm({ ...form, city: c })}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                    form.city === c ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
            <select
              value={CITIES.includes(form.city) ? "" : form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
              className="mt-2 w-full px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-600"
            >
              <option value="">Otra ciudad...</option>
              {CITIES.slice(10).map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <DollarSign className="h-4 w-4 text-gray-400" /> Rango de presupuesto objetivo
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {BUDGET_RANGES.map((r, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => selectBudgetRange(r)}
                  className={`px-3 py-2 rounded-lg border text-sm font-medium transition-all ${
                    form.budget_min == r.min && form.budget_max == r.max
                      ? "border-brand-500 bg-brand-50 text-brand-700"
                      : "border-gray-200 hover:border-gray-300 text-gray-600"
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>
            {currentBudgetLabel() && (
              <p className="text-xs text-brand-600 mt-2">Seleccionado: {currentBudgetLabel()}</p>
            )}
          </div>

          <div className="pt-2">
            <Button type="submit" disabled={saving} className="w-full sm:w-auto">
              <Save className="h-4 w-4" /> {saving ? "Guardando..." : "Guardar cambios"}
            </Button>
          </div>
        </form>
      </Card>

      {/* ── BÚSQUEDA & MATCHING ── */}
      <Card>
        <CardHeader title="Búsqueda y matching" subtitle="Ajusta cómo Jobper prioriza los contratos para ti" />
        <div className="space-y-5">
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Filter className="h-4 w-4 text-gray-400" /> Fuentes de contratos
            </label>
            <div className="flex flex-wrap gap-2">
              {SOURCES.map((s) => (
                <span key={s} className="px-3 py-1.5 bg-brand-50 text-brand-700 rounded-full text-sm font-medium border border-brand-100">
                  {s}
                </span>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">Próximamente: selecciona qué fuentes monitorear.</p>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <SlidersHorizontal className="h-4 w-4 text-gray-400" /> Tipos de contrato de interés
            </label>
            <div className="flex flex-wrap gap-2">
              {CONTRACT_TYPES.map((t) => (
                <span key={t} className="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-full text-sm border border-gray-200">
                  {t}
                </span>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">Próximamente: filtra por tipo de contrato.</p>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Search className="h-4 w-4 text-gray-400" /> Umbral mínimo de match (%)
            </label>
            <div className="flex items-center gap-3">
              <input type="range" min={0} max={80} step={5} defaultValue={0}
                className="flex-1 accent-brand-600" disabled />
              <span className="text-sm font-semibold text-gray-400 w-12">0%</span>
            </div>
            <p className="text-xs text-gray-400 mt-1">Próximamente: ocultar contratos con score menor a este valor.</p>
          </div>
        </div>
      </Card>

      {/* ── NOTIFICACIONES ── */}
      <Card>
        <CardHeader title="Notificaciones" subtitle="Cómo y cuándo te avisamos de nuevos contratos" />
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Push notifications</p>
              <p className="text-xs text-gray-500">Alertas en el navegador cuando aparecen contratos relevantes.</p>
            </div>
            <Button variant="secondary" size="sm" onClick={enablePush} disabled={pushEnabled}>
              <Bell className="h-4 w-4" /> {pushEnabled ? "Activado" : "Activar"}
            </Button>
          </div>

          <div className="border-t border-gray-100 pt-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Resumen diario por email</p>
              <p className="text-xs text-gray-500">Se envía automáticamente si hay contratos nuevos.</p>
            </div>
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">Automático</span>
          </div>

          <div className="border-t border-gray-100 pt-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-sm font-medium text-gray-900 flex items-center gap-1.5">
                  <MessageCircle className="h-4 w-4 text-green-600" /> WhatsApp
                </p>
                <p className="text-xs text-gray-500">Alertas de contratos por WhatsApp.</p>
              </div>
              <button
                type="button"
                onClick={() => setForm({ ...form, whatsapp_enabled: !form.whatsapp_enabled })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  form.whatsapp_enabled ? "bg-green-600" : "bg-gray-200"
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  form.whatsapp_enabled ? "translate-x-6" : "translate-x-1"
                }`} />
              </button>
            </div>
            {form.whatsapp_enabled && (
              <Input value={form.whatsapp_number}
                onChange={(e) => setForm({ ...form, whatsapp_number: e.target.value })}
                placeholder="+57 300 123 4567" />
            )}
          </div>

          <div className="border-t border-gray-100 pt-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">✈️</span>
              <p className="text-sm font-medium text-gray-900">Telegram</p>
            </div>
            <p className="text-xs text-gray-500 mb-3">
              Busca <span className="font-mono bg-gray-100 px-1 rounded">@JobperAlertas_bot</span> en Telegram
              y envía <span className="font-mono bg-gray-100 px-1 rounded">/start</span> para obtener tu Chat ID.
            </p>
            <Input
              placeholder="Chat ID de Telegram (ej: 123456789)"
              value={form.telegram_chat_id}
              onChange={(e) => setForm({ ...form, telegram_chat_id: e.target.value })}
            />
          </div>

          {(form.whatsapp_enabled || form.telegram_chat_id) && (
            <div className="pt-2">
              <Button onClick={save} disabled={saving} size="sm" variant="secondary">
                <Save className="h-4 w-4" /> Guardar notificaciones
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* ── SEGURIDAD ── */}
      <Card>
        <CardHeader title="Seguridad" subtitle="Contraseña y acceso a tu cuenta" />
        <form onSubmit={changePassword} className="space-y-4">
          <Input
            label="Contraseña actual"
            type={showPw ? "text" : "password"}
            placeholder="Deja en blanco si usas Magic Link"
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
              className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700"
            >
              {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              {showPw ? "Ocultar" : "Mostrar"}
            </button>
            <Button type="submit" size="sm" disabled={savingPw} className="ml-auto">
              <Lock className="h-4 w-4" />
              {savingPw ? "Guardando..." : "Cambiar contraseña"}
            </Button>
          </div>
          <p className="text-xs text-gray-400">Si usas Magic Link (sin contraseña), deja el campo actual en blanco.</p>
        </form>
      </Card>

      {/* ── PRIVACIDAD & DATOS ── */}
      <Card>
        <CardHeader title="Privacidad y datos" subtitle="Gestión de tu información personal (Ley 1581/2012)" />
        <div className="space-y-4">
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm font-medium text-gray-900">Exportar mis datos</p>
              <p className="text-xs text-gray-500">Copia de tus favoritos, pipeline y perfil.</p>
            </div>
            <Button variant="secondary" size="sm" onClick={() => {
              window.open("mailto:soporte@jobper.co?subject=Solicitud%20de%20exportación%20de%20datos", "_blank");
            }}>
              <Download className="h-4 w-4" /> Solicitar
            </Button>
          </div>

          <div className="border-t border-gray-100 pt-4 flex items-center justify-between py-2">
            <div>
              <p className="text-sm font-medium text-gray-900">Política de privacidad</p>
              <p className="text-xs text-gray-500">Cómo usamos y protegemos tus datos.</p>
            </div>
            <a href="/privacy" target="_blank" className="text-sm text-brand-600 hover:underline font-medium">
              Ver política →
            </a>
          </div>

          <div className="border-t border-gray-100 pt-4">
            <div className="p-4 bg-red-50 rounded-xl border border-red-100">
              <p className="text-sm font-semibold text-red-700 flex items-center gap-1.5 mb-1">
                <Trash2 className="h-4 w-4" /> Eliminar cuenta
              </p>
              <p className="text-xs text-red-600 mb-3">
                Irreversible. Elimina todos tus datos, favoritos, pipeline y suscripción activa. No se puede deshacer.
              </p>
              <Button
                variant="secondary"
                size="sm"
                className="border-red-200 text-red-600 hover:bg-red-100"
                onClick={async () => {
                  const confirmed = window.confirm(
                    `¿Eliminar permanentemente la cuenta de ${user?.email}?\n\nSe borrarán todos tus datos, favoritos, pipeline y suscripción. Esta acción es IRREVERSIBLE.`
                  );
                  if (!confirmed) return;
                  const reconfirmed = window.confirm("Última confirmación: ¿seguro que quieres eliminar tu cuenta para siempre?");
                  if (!reconfirmed) return;
                  try {
                    await api.del("/user/account");
                    window.location.href = "/";
                  } catch (err) {
                    toast.error(err.error || "Error eliminando cuenta. Escríbenos a soporte@jobper.co");
                  }
                }}
              >
                <Trash2 className="h-4 w-4" /> Eliminar permanentemente
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
