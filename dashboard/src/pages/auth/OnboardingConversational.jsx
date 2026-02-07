import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import {
  Sparkles,
  Building2,
  MapPin,
  Tag,
  DollarSign,
  Briefcase,
  Check,
  Edit3,
  ChevronRight,
  Wand2,
  MessageSquare,
  Zap,
  ArrowRight,
} from "lucide-react";

// =============================================================================
// CONFIGURACIÓN
// =============================================================================

const SECTORS = {
  tecnologia: { label: "Tecnología", icon: "💻" },
  construccion: { label: "Construcción", icon: "🏗️" },
  consultoria: { label: "Consultoría", icon: "📊" },
  salud: { label: "Salud", icon: "🏥" },
  educacion: { label: "Educación", icon: "📚" },
  logistica: { label: "Logística", icon: "🚛" },
  energia: { label: "Energía", icon: "⚡" },
  marketing: { label: "Marketing", icon: "📣" },
};

const BUDGET_LABELS = {
  micro: "Hasta $50M",
  small: "$50M - $200M",
  medium: "$200M - $500M",
  large: "$500M - $2.000M",
  xlarge: "Más de $2.000M",
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function OnboardingConversational() {
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const textareaRef = useRef(null);

  // Estados del flujo
  const [phase, setPhase] = useState("welcome"); // welcome, input, analyzing, confirm, saving
  const [userInput, setUserInput] = useState("");
  const [profile, setProfile] = useState(null);
  const [editingField, setEditingField] = useState(null);
  const [matchedCount, setMatchedCount] = useState(null);
  const [error, setError] = useState(null);

  // Auto-focus en textarea
  useEffect(() => {
    if (phase === "input" && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [phase]);

  // Analizar texto con IA
  const analyzeWithAI = async () => {
    if (!userInput.trim()) return;

    setPhase("analyzing");
    setError(null);

    try {
      const result = await api.post("/onboarding/analyze", {
        description: userInput,
      });

      if (result.error) {
        setError(result.error);
        setPhase("input");
        return;
      }

      setProfile(result.profile);
      setMatchedCount(result.matched_preview || 0);
      setPhase("confirm");
    } catch (err) {
      console.error("AI analysis failed:", err);
      setError("No pudimos analizar tu descripción. Intenta de nuevo o usa el formulario tradicional.");
      setPhase("input");
    }
  };

  // Guardar perfil y continuar
  const saveProfile = async () => {
    if (!profile) return;

    setPhase("saving");

    try {
      await api.put("/user/profile", {
        company_name: profile.company_name,
        sector: profile.sector,
        keywords: profile.keywords,
        city: profile.city,
        budget_min: profile.budget_min,
        budget_max: profile.budget_max,
      });

      await refresh();
      navigate("/dashboard", { replace: true });
    } catch (err) {
      console.error("Save failed:", err);
      setError("Error guardando tu perfil. Intenta de nuevo.");
      setPhase("confirm");
    }
  };

  // Actualizar campo del perfil
  const updateField = (field, value) => {
    setProfile((p) => ({ ...p, [field]: value }));
    setEditingField(null);
  };

  // Ir al onboarding tradicional
  const goToTraditional = () => {
    navigate("/onboarding/traditional", { replace: true });
  };

  // Saltar onboarding
  const skip = () => {
    navigate("/dashboard", { replace: true });
  };

  // =============================================================================
  // RENDER PHASES
  // =============================================================================

  // Welcome Phase
  if (phase === "welcome") {
    return (
      <OnboardingLayout>
        <div className="text-center space-y-8 animate-fadeIn">
          {/* Logo/Icon */}
          <div className="relative inline-block">
            <div className="w-24 h-24 bg-gradient-to-br from-brand-500 to-purple-600 rounded-3xl flex items-center justify-center shadow-xl">
              <Sparkles className="h-12 w-12 text-white" />
            </div>
            <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center shadow-lg">
              <Wand2 className="h-4 w-4 text-white" />
            </div>
          </div>

          {/* Welcome message */}
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              ¡Bienvenido a Jobper!
            </h1>
            <p className="mt-3 text-lg text-gray-600 max-w-md mx-auto">
              Vamos a encontrar los contratos perfectos para tu empresa en menos de 1 minuto.
            </p>
          </div>

          {/* CTA */}
          <Button
            size="lg"
            className="px-8 py-4 text-lg"
            onClick={() => setPhase("input")}
          >
            Empezar
            <ArrowRight className="h-5 w-5 ml-2" />
          </Button>
        </div>
      </OnboardingLayout>
    );
  }

  // Input Phase - Textarea conversacional
  if (phase === "input") {
    return (
      <OnboardingLayout>
        <div className="space-y-6 animate-fadeIn">
          {/* Header */}
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-brand-100 rounded-2xl mb-4">
              <MessageSquare className="h-7 w-7 text-brand-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              Cuéntame sobre tu empresa
            </h1>
            <p className="mt-2 text-gray-500">
              Describe en tus propias palabras qué hace tu empresa y qué contratos buscan
            </p>
          </div>

          {/* Textarea */}
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Ej: Somos una empresa de construcción en Medellín, hacemos obras civiles, pavimentación y mantenimiento vial. Nos interesan contratos con alcaldías y gobernaciones de Antioquia entre 500 y 5000 millones..."
              className="w-full h-40 p-4 text-base border-2 border-gray-200 rounded-2xl resize-none focus:border-brand-500 focus:ring-4 focus:ring-brand-100 transition-all"
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.metaKey) {
                  analyzeWithAI();
                }
              }}
            />
            <p className="absolute bottom-3 right-3 text-xs text-gray-400">
              ⌘ + Enter para analizar
            </p>
          </div>

          {/* Error message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Examples */}
          <div className="bg-gray-50 rounded-xl p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Ejemplos de lo que puedes escribir:
            </p>
            <div className="space-y-2 text-sm text-gray-600">
              <p>• "Vendemos software y servicios cloud para empresas grandes"</p>
              <p>• "Hacemos consultoría en gestión ambiental para mineras"</p>
              <p>• "Proveemos equipos médicos a hospitales del Valle"</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              variant="secondary"
              onClick={goToTraditional}
              className="flex-shrink-0"
            >
              Formulario tradicional
            </Button>
            <Button
              className="flex-1"
              onClick={analyzeWithAI}
              disabled={!userInput.trim()}
            >
              <Wand2 className="h-4 w-4 mr-2" />
              Analizar con IA
            </Button>
          </div>

          <button
            onClick={skip}
            className="w-full text-sm text-gray-400 hover:text-gray-600 transition"
          >
            Saltar por ahora
          </button>
        </div>
      </OnboardingLayout>
    );
  }

  // Analyzing Phase
  if (phase === "analyzing") {
    return (
      <OnboardingLayout>
        <div className="text-center space-y-8 animate-fadeIn">
          <div className="relative inline-block">
            <div className="w-20 h-20 bg-gradient-to-br from-brand-500 to-purple-600 rounded-2xl flex items-center justify-center animate-pulse">
              <Wand2 className="h-10 w-10 text-white animate-bounce" />
            </div>
          </div>

          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Analizando tu empresa...
            </h2>
            <p className="mt-2 text-gray-500">
              Nuestra IA está extrayendo la información clave
            </p>
          </div>

          <div className="flex justify-center">
            <Spinner className="h-8 w-8 text-brand-600" />
          </div>

          <div className="space-y-2 text-sm text-gray-400">
            <p className="animate-pulse">🔍 Identificando sector...</p>
            <p className="animate-pulse delay-100">📍 Detectando ubicación...</p>
            <p className="animate-pulse delay-200">💰 Analizando presupuesto...</p>
          </div>
        </div>
      </OnboardingLayout>
    );
  }

  // Confirm Phase
  if (phase === "confirm") {
    return (
      <OnboardingLayout>
        <div className="space-y-6 animate-fadeIn">
          {/* Header */}
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-green-100 rounded-2xl mb-4">
              <Check className="h-7 w-7 text-green-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              ¡Listo! Esto es lo que entendí
            </h1>
            <p className="mt-2 text-gray-500">
              Revisa y ajusta si algo no es correcto
            </p>
          </div>

          {/* Profile cards */}
          <div className="space-y-3">
            <ProfileField
              icon={Building2}
              label="Empresa"
              value={profile?.company_name}
              onEdit={() => setEditingField("company_name")}
              editing={editingField === "company_name"}
              onSave={(v) => updateField("company_name", v)}
            />

            <ProfileField
              icon={Briefcase}
              label="Sector"
              value={SECTORS[profile?.sector]?.label || profile?.sector}
              valueIcon={SECTORS[profile?.sector]?.icon}
              onEdit={() => setEditingField("sector")}
              editing={editingField === "sector"}
              onSave={(v) => updateField("sector", v)}
              options={Object.entries(SECTORS).map(([k, v]) => ({
                value: k,
                label: `${v.icon} ${v.label}`,
              }))}
            />

            <ProfileField
              icon={Tag}
              label="Palabras clave"
              value={profile?.keywords?.join(", ")}
              onEdit={() => setEditingField("keywords")}
              editing={editingField === "keywords"}
              onSave={(v) => updateField("keywords", v.split(",").map((k) => k.trim()))}
            />

            <ProfileField
              icon={MapPin}
              label="Ciudad"
              value={profile?.city || "No especificada"}
              onEdit={() => setEditingField("city")}
              editing={editingField === "city"}
              onSave={(v) => updateField("city", v)}
            />

            <ProfileField
              icon={DollarSign}
              label="Presupuesto"
              value={getBudgetLabel(profile?.budget_min, profile?.budget_max)}
              onEdit={() => setEditingField("budget")}
              editing={editingField === "budget"}
              onSave={(v) => {
                const [min, max] = parseBudget(v);
                updateField("budget_min", min);
                updateField("budget_max", max);
              }}
            />
          </div>

          {/* Matched count preview */}
          {matchedCount > 0 && (
            <div className="bg-gradient-to-r from-brand-50 to-purple-50 border border-brand-200 rounded-2xl p-4 text-center">
              <div className="flex items-center justify-center gap-2 text-brand-700">
                <Zap className="h-5 w-5" />
                <span className="font-bold text-lg">{matchedCount} contratos</span>
              </div>
              <p className="text-sm text-brand-600 mt-1">
                coinciden con tu perfil ahora mismo
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setPhase("input")}>
              Volver a escribir
            </Button>
            <Button className="flex-1" onClick={saveProfile}>
              Ver mis contratos
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      </OnboardingLayout>
    );
  }

  // Saving Phase
  if (phase === "saving") {
    return (
      <OnboardingLayout>
        <div className="text-center space-y-6 animate-fadeIn">
          <Spinner className="h-12 w-12 text-brand-600 mx-auto" />
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Preparando tu feed personalizado...
            </h2>
            <p className="mt-2 text-gray-500">
              Buscando los mejores contratos para ti
            </p>
          </div>
        </div>
      </OnboardingLayout>
    );
  }

  return null;
}

// =============================================================================
// SUBCOMPONENTS
// =============================================================================

function OnboardingLayout({ children }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 via-white to-purple-50 px-4 py-12">
      <div className="w-full max-w-lg">
        {children}
      </div>
    </div>
  );
}

function ProfileField({ icon: Icon, label, value, valueIcon, onEdit, editing, onSave, options }) {
  const [editValue, setEditValue] = useState(value);

  useEffect(() => {
    setEditValue(value);
  }, [value]);

  if (editing) {
    return (
      <div className="bg-white border-2 border-brand-500 rounded-xl p-4 space-y-3">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        {options ? (
          <select
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            className="w-full p-2 border rounded-lg"
            autoFocus
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            className="w-full p-2 border rounded-lg"
            autoFocus
          />
        )}
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={() => onSave(value)}>
            Cancelar
          </Button>
          <Button size="sm" onClick={() => onSave(editValue)}>
            Guardar
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onEdit}
      className="flex items-center gap-4 bg-white border border-gray-200 rounded-xl p-4 cursor-pointer hover:border-brand-300 hover:bg-brand-50/50 transition group"
    >
      <div className="flex-shrink-0 w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-brand-100 transition">
        <Icon className="h-5 w-5 text-gray-500 group-hover:text-brand-600" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
        <p className="text-sm font-medium text-gray-900 truncate flex items-center gap-1">
          {valueIcon && <span>{valueIcon}</span>}
          {value || "No especificado"}
        </p>
      </div>
      <Edit3 className="h-4 w-4 text-gray-300 group-hover:text-brand-500" />
    </div>
  );
}

// =============================================================================
// HELPERS
// =============================================================================

function getBudgetLabel(min, max) {
  if (!min && !max) return "Cualquier monto";
  if (min === 0 && max === 50000000) return "Hasta $50M";
  if (min === 50000000 && max === 200000000) return "$50M - $200M";
  if (min === 200000000 && max === 500000000) return "$200M - $500M";
  if (min === 500000000 && max === 2000000000) return "$500M - $2.000M";
  if (min >= 2000000000) return "Más de $2.000M";
  if (min && max) return `$${(min / 1000000).toFixed(0)}M - $${(max / 1000000).toFixed(0)}M`;
  if (min) return `Desde $${(min / 1000000).toFixed(0)}M`;
  if (max) return `Hasta $${(max / 1000000).toFixed(0)}M`;
  return "Cualquier monto";
}

function parseBudget(label) {
  // Parse budget label back to min/max
  if (label.includes("Hasta $50M")) return [0, 50000000];
  if (label.includes("$50M - $200M")) return [50000000, 200000000];
  if (label.includes("$200M - $500M")) return [200000000, 500000000];
  if (label.includes("$500M - $2.000M")) return [500000000, 2000000000];
  if (label.includes("Más de $2.000M")) return [2000000000, null];
  return [null, null];
}

// Add CSS animation in index.css or tailwind
// @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
// .animate-fadeIn { animation: fadeIn 0.4s ease-out; }
