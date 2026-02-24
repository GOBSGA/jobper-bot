import { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import Card, { CardHeader } from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import { useToast } from "../../components/ui/Toast";
import { Save, Bell, Building2, MapPin, DollarSign, Tag, User, MessageCircle, Lock, Eye, EyeOff } from "lucide-react";

const SECTORS = [
  { key: "tecnologia", label: "Tecnología", emoji: "💻" },
  { key: "construccion", label: "Construcción", emoji: "🏗️" },
  { key: "salud", label: "Salud", emoji: "🏥" },
  { key: "educacion", label: "Educación", emoji: "📚" },
  { key: "consultoria", label: "Consultoría", emoji: "📊" },
  { key: "logistica", label: "Logística", emoji: "🚚" },
  { key: "marketing", label: "Marketing", emoji: "📢" },
  { key: "energia", label: "Energía", emoji: "⚡" },
];

const CITIES = [
  "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
  "Bucaramanga", "Pereira", "Santa Marta", "Manizales", "Cúcuta",
  "Ibagué", "Villavicencio", "Pasto", "Montería", "Neiva",
];

const BUDGET_RANGES = [
  { min: 0, max: 50_000_000, label: "Hasta $50M" },
  { min: 50_000_000, max: 200_000_000, label: "$50M - $200M" },
  { min: 200_000_000, max: 500_000_000, label: "$200M - $500M" },
  { min: 500_000_000, max: 2_000_000_000, label: "$500M - $2.000M" },
  { min: 2_000_000_000, max: null, label: "Más de $2.000M" },
];

export default function Settings() {
  const { user, refresh } = useAuth();
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
    e.preventDefault();
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

  const selectBudgetRange = (range) => {
    setForm({
      ...form,
      budget_min: range.min || "",
      budget_max: range.max || "",
    });
  };

  const changePassword = async (e) => {
    e.preventDefault();
    if (!pwForm.current) {
      toast.error("Ingresa tu contraseña actual");
      return;
    }
    if (pwForm.next.length < 8) {
      toast.error("La nueva contraseña debe tener al menos 8 caracteres");
      return;
    }
    if (pwForm.next !== pwForm.confirm) {
      toast.error("Las contraseñas no coinciden");
      return;
    }
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
      if (!reg) return;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: import.meta.env.VITE_VAPID_PUBLIC_KEY,
      });
      await api.post("/user/push-subscription", sub.toJSON());
      setPushEnabled(true);
      toast.success("Notificaciones push activadas");
    } catch {
      toast.error("No se pudo activar push notifications.");
    }
  };

  const currentBudgetLabel = () => {
    if (!form.budget_min && !form.budget_max) return null;
    const found = BUDGET_RANGES.find(
      (r) => r.min === form.budget_min && r.max === form.budget_max
    );
    return found?.label || `$${(form.budget_min/1_000_000).toFixed(0)}M - $${form.budget_max ? (form.budget_max/1_000_000).toFixed(0) + "M" : "∞"}`;
  };

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Configuración</h1>

      {/* Perfil de empresa */}
      <Card>
        <CardHeader title="Perfil de empresa" subtitle="Información para encontrar contratos relevantes" />
        <form onSubmit={save} className="space-y-5">
          {/* Email (readonly) */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <User className="h-4 w-4 text-gray-400" /> Email
            </label>
            <Input value={user?.email || ""} disabled className="bg-gray-50" />
          </div>

          {/* Empresa */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <Building2 className="h-4 w-4 text-gray-400" /> Nombre de empresa
            </label>
            <Input
              value={form.company_name}
              onChange={(e) => setForm({ ...form, company_name: e.target.value })}
              placeholder="Mi Empresa S.A.S."
            />
          </div>

          {/* Sector */}
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

          {/* Palabras clave */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <Tag className="h-4 w-4 text-gray-400" /> Palabras clave
            </label>
            <Input
              value={form.keywords}
              onChange={(e) => setForm({ ...form, keywords: e.target.value })}
              placeholder="software, desarrollo, cloud, IA"
            />
            <p className="text-xs text-gray-500 mt-1">Separadas por coma. Usamos estas para encontrar contratos relevantes.</p>
          </div>

          {/* Ciudad */}
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
                    form.city === c
                      ? "bg-brand-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
            {/* Otras ciudades */}
            <div className="mt-2">
              <select
                value={CITIES.includes(form.city) ? "" : form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-600"
              >
                <option value="">Otra ciudad...</option>
                {CITIES.slice(10).map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Rango de presupuesto */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <DollarSign className="h-4 w-4 text-gray-400" /> Rango de presupuesto
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

      {/* Cambiar contraseña */}
      <Card>
        <CardHeader title="Seguridad" subtitle="Cambia tu contraseña de acceso" />
        <form onSubmit={changePassword} className="space-y-4">
          <div className="relative">
            <Input
              label="Contraseña actual"
              type={showPw ? "text" : "password"}
              placeholder="Deja en blanco si usas Magic Link"
              value={pwForm.current}
              onChange={(e) => setPwForm({ ...pwForm, current: e.target.value })}
            />
          </div>
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
            placeholder="Repite la nueva contraseña"
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
              {showPw ? "Ocultar" : "Mostrar"} contraseñas
            </button>
            <Button type="submit" size="sm" disabled={savingPw} className="ml-auto">
              <Lock className="h-4 w-4" />
              {savingPw ? "Guardando..." : "Cambiar contraseña"}
            </Button>
          </div>
          <p className="text-xs text-gray-400">
            Si creaste tu cuenta con Magic Link (sin contraseña), puedes dejar "Contraseña actual" en blanco.
          </p>
        </form>
      </Card>

      {/* Notificaciones */}
      <Card>
        <CardHeader title="Notificaciones" subtitle="Configura cómo quieres recibir alertas" />
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Push notifications</p>
              <p className="text-xs text-gray-500">Recibe alertas de contratos en tu navegador.</p>
            </div>
            <Button variant="secondary" size="sm" onClick={enablePush} disabled={pushEnabled}>
              <Bell className="h-4 w-4" /> {pushEnabled ? "Activado" : "Activar"}
            </Button>
          </div>

          <div className="border-t border-gray-100 pt-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-sm font-medium text-gray-900 flex items-center gap-1.5">
                  <MessageCircle className="h-4 w-4 text-green-600" /> WhatsApp
                </p>
                <p className="text-xs text-gray-500">Recibe alertas de contratos por WhatsApp.</p>
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
              <Input
                value={form.whatsapp_number}
                onChange={(e) => setForm({ ...form, whatsapp_number: e.target.value })}
                placeholder="+57 300 123 4567"
              />
            )}
            {form.whatsapp_enabled && form.whatsapp_number && (
              <p className="text-xs text-gray-500 mt-1">Guarda los cambios para activar WhatsApp.</p>
            )}
          </div>

          <div className="border-t border-gray-100 pt-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">✈️</span>
              <p className="text-sm font-medium text-gray-900">Telegram</p>
            </div>
            <p className="text-xs text-gray-500 mb-3">
              Recibe alertas de contratos en Telegram. Pasos:
              {" "}<strong>1)</strong> Busca <span className="font-mono bg-gray-100 px-1 rounded">@JobperAlertas_bot</span> en Telegram y envía{" "}
              <span className="font-mono bg-gray-100 px-1 rounded">/start</span> o{" "}
              <span className="font-mono bg-gray-100 px-1 rounded">/vincular {user?.email}</span>.
              {" "}<strong>2)</strong> El bot te dará tu Chat ID. Pégalo aquí y guarda.
            </p>
            <Input
              placeholder="Tu Chat ID de Telegram (ej: 123456789)"
              value={form.telegram_chat_id}
              onChange={(e) => setForm({ ...form, telegram_chat_id: e.target.value })}
            />
            {form.telegram_chat_id && (
              <p className="text-xs text-green-600 mt-1">Guarda los cambios para activar Telegram.</p>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
