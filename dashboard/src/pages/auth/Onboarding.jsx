import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import { useToast } from "../../components/ui/Toast";
import { Building2, Briefcase, Tag, MapPin, DollarSign, ChevronRight, ChevronLeft, Sparkles } from "lucide-react";

const SECTORS = [
  { key: "tecnologia", label: "Tecnología e Informática", icon: "💻" },
  { key: "construccion", label: "Construcción e Infraestructura", icon: "🏗️" },
  { key: "consultoria", label: "Consultoría y Servicios", icon: "📊" },
  { key: "salud", label: "Salud y Farmacéutica", icon: "🏥" },
  { key: "educacion", label: "Educación y Capacitación", icon: "📚" },
  { key: "logistica", label: "Logística y Transporte", icon: "🚛" },
  { key: "energia", label: "Energía y Medio Ambiente", icon: "⚡" },
  { key: "marketing", label: "Marketing y Comunicaciones", icon: "📣" },
];

const BUDGET_RANGES = [
  { key: "micro", label: "Hasta $50M", min: 0, max: 50000000 },
  { key: "small", label: "$50M - $200M", min: 50000000, max: 200000000 },
  { key: "medium", label: "$200M - $500M", min: 200000000, max: 500000000 },
  { key: "large", label: "$500M - $2.000M", min: 500000000, max: 2000000000 },
  { key: "xlarge", label: "Más de $2.000M", min: 2000000000, max: null },
  { key: "any", label: "Cualquier monto", min: 0, max: null },
];

const CITIES = [
  "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
  "Bucaramanga", "Pereira", "Manizales", "Santa Marta", "Ibagué",
  "Villavicencio", "Pasto", "Neiva", "Armenia", "Cúcuta",
];

const KEYWORD_SUGGESTIONS = {
  tecnologia: ["software", "desarrollo web", "cloud", "ciberseguridad", "apps móviles", "infraestructura TI", "bases de datos", "inteligencia artificial"],
  construccion: ["obra civil", "edificio", "carretera", "puente", "acueducto", "remodelación", "interventoría", "urbanismo"],
  consultoria: ["asesoría", "auditoría", "gestión", "interventoría", "diagnóstico", "evaluación", "due diligence", "estrategia"],
  salud: ["equipos médicos", "insumos", "laboratorio", "medicamentos", "ambulancias", "dispositivos médicos", "vacunas"],
  educacion: ["capacitación", "formación", "e-learning", "material educativo", "diplomado", "taller", "investigación"],
  logistica: ["transporte", "distribución", "almacenamiento", "flota", "mensajería", "inventario", "cadena de suministro"],
  energia: ["energía solar", "renovable", "gestión ambiental", "residuos", "reciclaje", "eficiencia energética", "saneamiento"],
  marketing: ["publicidad", "redes sociales", "diseño", "branding", "eventos", "producción audiovisual", "contenido"],
};

export default function Onboarding() {
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const toast = useToast();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    company_name: "",
    sector: "",
    keywords: [],
    city: "",
    budget_min: null,
    budget_max: null,
  });

  const steps = [
    { title: "¿Cómo se llama tu empresa?", subtitle: "Esto personaliza tu experiencia", icon: Building2 },
    { title: "¿En qué sector trabajas?", subtitle: "Te mostraremos contratos relevantes a tu industria", icon: Briefcase },
    { title: "¿Qué servicios ofreces?", subtitle: "Selecciona o escribe palabras clave de lo que vendes", icon: Tag },
    { title: "¿En qué rango de presupuesto licitas?", subtitle: "Filtramos contratos a tu medida", icon: DollarSign },
    { title: "¿En qué ciudad operas?", subtitle: "Priorizamos contratos cerca de ti", icon: MapPin },
  ];

  const canNext = () => {
    switch (step) {
      case 0: return form.company_name.trim().length > 0;
      case 1: return form.sector.length > 0;
      default: return true;
    }
  };

  const submit = async () => {
    setLoading(true);
    try {
      await api.put("/user/profile", {
        company_name: form.company_name,
        sector: form.sector,
        keywords: form.keywords,
        city: form.city || undefined,
        budget_min: form.budget_min,
        budget_max: form.budget_max,
      });
      await api.post("/onboarding/complete", {});
      await refresh();
      navigate("/dashboard", { replace: true });
    } catch (err) {
      toast.error(err.error || "Error al guardar tu perfil. Intenta de nuevo.");
      setLoading(false);
    }
  };

  const next = () => {
    if (step < steps.length - 1) setStep(step + 1);
    else submit();
  };

  const currentStep = steps[step];
  const Icon = currentStep.icon;
  const suggestions = KEYWORD_SUGGESTIONS[form.sector] || [];

  const toggleKeyword = (kw) => {
    setForm((f) => ({
      ...f,
      keywords: f.keywords.includes(kw)
        ? f.keywords.filter((k) => k !== kw)
        : [...f.keywords, kw],
    }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 via-white to-purple-50 px-4">
      <div className="w-full max-w-lg">
        {/* Progress */}
        <div className="flex gap-1.5 mb-8">
          {steps.map((_, i) => (
            <div key={i} className={`h-1.5 flex-1 rounded-full transition-all ${i <= step ? "bg-brand-600" : "bg-gray-200"}`} />
          ))}
        </div>

        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-brand-100 rounded-2xl mb-4">
            <Icon className="h-7 w-7 text-brand-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{currentStep.title}</h1>
          <p className="mt-1 text-sm text-gray-500">{currentStep.subtitle}</p>
        </div>

        {/* Step content */}
        <div className="mb-8">
          {step === 0 && (
            <Input
              value={form.company_name}
              onChange={(e) => setForm({ ...form, company_name: e.target.value })}
              placeholder="Mi Empresa SAS"
              autoFocus
              onKeyDown={(e) => e.key === "Enter" && canNext() && next()}
            />
          )}

          {step === 1 && (
            <div className="grid grid-cols-2 gap-3">
              {SECTORS.map((s) => (
                <button
                  key={s.key}
                  onClick={() => { setForm({ ...form, sector: s.key }); setTimeout(() => setStep(2), 200); }}
                  className={`flex items-center gap-3 p-3 rounded-xl border-2 text-left text-sm font-medium transition ${
                    form.sector === s.key
                      ? "border-brand-600 bg-brand-50 text-brand-800"
                      : "border-gray-200 hover:border-gray-300 text-gray-700"
                  }`}
                >
                  <span className="text-xl">{s.icon}</span>
                  <span className="leading-tight">{s.label}</span>
                </button>
              ))}
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              {suggestions.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {suggestions.map((kw) => (
                    <button
                      key={kw}
                      onClick={() => toggleKeyword(kw)}
                      className={`px-3 py-1.5 rounded-full text-sm font-medium transition ${
                        form.keywords.includes(kw)
                          ? "bg-brand-600 text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      {kw}
                    </button>
                  ))}
                </div>
              )}
              <Input
                placeholder="O escribe palabras clave separadas por coma y presiona Enter"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && e.target.value.trim()) {
                    const newKws = e.target.value.split(",").map((k) => k.trim()).filter(Boolean);
                    setForm({ ...form, keywords: [...new Set([...form.keywords, ...newKws])] });
                    e.target.value = "";
                  }
                }}
              />
              {form.keywords.length > 0 && (
                <p className="text-xs text-gray-500">{form.keywords.length} seleccionadas: {form.keywords.join(", ")}</p>
              )}
            </div>
          )}

          {step === 3 && (
            <div className="space-y-3">
              {BUDGET_RANGES.map((b) => (
                <button
                  key={b.key}
                  onClick={() => { setForm({ ...form, budget_min: b.min, budget_max: b.max }); setTimeout(() => setStep(4), 200); }}
                  className={`w-full flex items-center gap-3 p-3 rounded-xl border-2 text-left text-sm font-medium transition ${
                    form.budget_min === b.min && form.budget_max === b.max
                      ? "border-brand-600 bg-brand-50 text-brand-800"
                      : "border-gray-200 hover:border-gray-300 text-gray-700"
                  }`}
                >
                  <DollarSign className="h-4 w-4 text-gray-400" />
                  {b.label}
                </button>
              ))}
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-2">
                {CITIES.map((city) => (
                  <button
                    key={city}
                    onClick={() => setForm({ ...form, city: form.city === city ? "" : city })}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                      form.city === city
                        ? "bg-brand-600 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    {city}
                  </button>
                ))}
              </div>
              <Input
                placeholder="O escribe otra ciudad..."
                value={CITIES.includes(form.city) ? "" : form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
              />
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex gap-3">
          {step > 0 && (
            <Button variant="secondary" onClick={() => setStep(step - 1)}>
              <ChevronLeft className="h-4 w-4" /> Atrás
            </Button>
          )}
          <Button className="flex-1" onClick={next} disabled={!canNext() || loading}>
            {loading ? "Preparando tu feed..." : step < steps.length - 1 ? (
              <>Siguiente <ChevronRight className="h-4 w-4" /></>
            ) : (
              <>Ver mis contratos <Sparkles className="h-4 w-4" /></>
            )}
          </Button>
        </div>

        {step === 0 && (
          <button onClick={() => navigate("/dashboard")} className="w-full text-sm text-gray-400 hover:underline mt-4 text-center">
            Saltar por ahora
          </button>
        )}
      </div>
    </div>
  );
}
