import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Button from "../../components/ui/Button";
import Logo from "../../components/ui/Logo";
import Spinner from "../../components/ui/Spinner";
import { Check, Zap, Shield, Search, GitBranch, Store, Bell, Users, ArrowRight, Star, MapPin, FileText, Calendar, Building2, Brain, Sparkles, MessageSquare, Trophy } from "lucide-react";

const FEATURES = [
  { icon: Brain, title: "Recomendaciones IA", desc: "Cada día analizamos todos los contratos y te decimos cuáles son los más óptimos para tu empresa. Una sola llamada a IA, costo casi $0.", color: "bg-purple-50 text-purple-600" },
  { icon: Search, title: "Búsqueda inteligente", desc: "Escribe lo que buscas en lenguaje natural. Entiende presupuesto, ciudad, sector y más sin filtros manuales.", color: "bg-brand-50 text-brand-600" },
  { icon: GitBranch, title: "Pipeline CRM", desc: "Lleva cada oportunidad desde Lead hasta Ganado. Notas, valores y seguimiento. Sin Excel, sin perder nada.", color: "bg-accent-50 text-accent-600" },
  { icon: Store, title: "Marketplace con chat", desc: "Publica contratos privados, conecta con proveedores y negocia directamente dentro de Jobper.", color: "bg-green-50 text-green-600" },
  { icon: Bell, title: "Alertas en tiempo real", desc: "Te avisamos al instante por email, push, WhatsApp y Telegram cuando aparezca una oportunidad relevante.", color: "bg-yellow-50 text-yellow-600" },
  { icon: Sparkles, title: "Análisis IA por contrato", desc: "Abre cualquier contrato y pide un análisis: tipo, complejidad, competencia, requisitos y probabilidad de ganar.", color: "bg-pink-50 text-pink-600" },
  { icon: MessageSquare, title: "Soporte IA 24/7", desc: "Asistente virtual entrenado en licitaciones colombianas: estrategia, AIU, consorcios, SECOP. Sin esperar a nadie.", color: "bg-blue-50 text-blue-600" },
  { icon: Shield, title: "Seguridad real", desc: "Auth sin contraseñas, tokens JWT rotativos, rate limiting, auditoría completa. Cumplimiento Ley 1581.", color: "bg-red-50 text-red-600" },
  { icon: Users, title: "Programa de referidos", desc: "Invita colegas y obtén descuentos acumulables. Ellos también ganan desde el primer mes.", color: "bg-indigo-50 text-indigo-600" },
];

const SOURCES = [
  { name: "SECOP I & II", desc: "Gobierno" },
  { name: "BID", desc: "Multilateral" },
  { name: "Banco Mundial", desc: "Multilateral" },
  { name: "Ecopetrol", desc: "Privado" },
  { name: "EPM", desc: "Privado" },
  { name: "ONU (UNGM)", desc: "Multilateral" },
  { name: "Colombia Compra", desc: "Gobierno" },
  { name: "Contratación en Línea", desc: "Gobierno" },
  { name: "SICE", desc: "Gobierno" },
  { name: "Bolsa Mercantil", desc: "Privado" },
  { name: "ISA", desc: "Privado" },
  { name: "Acueducto Bogotá", desc: "Público" },
];

const PLANS = [
  {
    name: "Observador", emoji: "👀", price: "Gratis",
    features: ["Ver contratos públicos", "10 búsquedas/día", "10 favoritos", "Asistente IA básico"],
  },
  {
    name: "Cazador", emoji: "🎯", price: "$29.900",
    features: ["Búsquedas ilimitadas", "Descripciones completas", "Match score real", "50 alertas/semana", "Exportar 50/mes a Excel", "Recomendaciones IA diarias"],
  },
  {
    name: "Competidor", emoji: "⚔️", price: "$149.900", popular: true,
    features: ["Todo de Cazador +", "Contratos PRIVADOS", "Pipeline CRM", "Alertas push instantáneas", "Análisis IA por contrato", "Marketplace con chat", "Exportar 500/mes"],
  },
  {
    name: "Estratega", emoji: "🚀", price: "$299.900",
    features: ["Todo de Competidor +", "2 usuarios en equipo", "Historial 2 años", "Reportes automáticos", "Soporte prioritario 12h"],
  },
  {
    name: "Dominador", emoji: "👑", price: "$599.900",
    features: ["Todo de Estratega +", "5 usuarios", "Inteligencia competitiva", "Auto-propuestas IA", "API access", "Soporte WhatsApp 4h", "Consultoría mensual"],
  },
];

const TESTIMONIALS = [
  { name: "Carlos Mendoza", role: "Ingeniero civil — Bogotá", text: "La IA me dice cada mañana cuáles son mis mejores contratos del día. En mi primera semana encontré 3 licitaciones que no había visto en SECOP.", avatar: "CM" },
  { name: "Ana Rodríguez", role: "Consultora TI — Medellín", text: "El Pipeline me salvó. Antes tenía todo en Excel y perdía oportunidades. El chat del Marketplace me conectó con mi primer subcontratista en 2 horas.", avatar: "AR" },
  { name: "Luis Parra", role: "Arquitecto — Cali", text: "Las alertas me llegan antes que a la competencia. El análisis IA me dice exactamente qué requisitos cumplir. Ya gané 2 contratos este mes.", avatar: "LP" },
];

const API_BASE = import.meta.env.VITE_API_URL || "/api";

export default function Landing() {
  const [demoContracts, setDemoContracts] = useState([]);
  const [demoStats, setDemoStats] = useState(null);
  const [loadingDemo, setLoadingDemo] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/public/demo`)
      .then((r) => r.json())
      .then((data) => {
        setDemoContracts(data.contracts || []);
        setDemoStats(data.stats || null);
      })
      .catch(() => {})
      .finally(() => setLoadingDemo(false));
  }, []);

  const formatMoney = (v) => v ? new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(v) : "—";
  const formatDate = (d) => d ? new Date(d).toLocaleDateString("es-CO", { day: "numeric", month: "short" }) : "—";

  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="sticky top-0 z-30 glass">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <Logo size={36} />
            <span className="text-xl font-bold tracking-tight">Jobper</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#features" className="text-sm text-gray-600 hover:text-gray-900 hidden sm:block transition">Funciones</a>
            <a href="#demo" className="text-sm text-gray-600 hover:text-gray-900 hidden sm:block transition">Demo</a>
            <a href="#pricing" className="text-sm text-gray-600 hover:text-gray-900 hidden sm:block transition">Precios</a>
            <Link to="/login"><Button size="sm">Comenzar gratis</Button></Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero-gradient relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23000' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")" }} />
        <div className="max-w-4xl mx-auto text-center px-6 pt-24 pb-20 relative">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-50 text-brand-700 text-sm font-medium mb-6 border border-brand-100">
            <MapPin className="h-4 w-4" />
            Hecho en Colombia, para Colombia
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-gray-900 leading-[1.1] tracking-tight">
            Deja de buscar contratos.<br />
            <span className="bg-gradient-to-r from-brand-600 to-accent-600 bg-clip-text text-transparent">Deja que te encuentren.</span>
          </h1>
          <p className="mt-6 text-lg sm:text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed">
            La plataforma colombiana que reúne contratos de SECOP, BID, Banco Mundial y 9 fuentes más.
            IA que te dice cada día cuáles son tus mejores oportunidades. Pipeline, Marketplace y alertas — todo en un solo lugar.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row justify-center gap-4">
            <Link to="/login">
              <Button size="lg" className="shadow-lg shadow-brand-500/25 hover:shadow-xl hover:shadow-brand-500/30 transition-all">
                <Zap className="h-5 w-5" /> Empezar — es gratis
              </Button>
            </Link>
            <a href="#features">
              <Button size="lg" variant="secondary">
                Cómo funciona <ArrowRight className="h-4 w-4" />
              </Button>
            </a>
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-sm text-gray-400">
            <span className="flex items-center gap-1"><Check className="h-4 w-4 text-accent-500" /> 14 días gratis</span>
            <span className="flex items-center gap-1"><Check className="h-4 w-4 text-accent-500" /> Sin tarjeta</span>
            <span className="flex items-center gap-1"><Check className="h-4 w-4 text-accent-500" /> Cancela cuando quieras</span>
          </div>

          {/* Stats */}
          <div className="mt-16 grid grid-cols-3 gap-6 max-w-lg mx-auto">
            <div>
              <p className="text-3xl font-extrabold text-gray-900">12+</p>
              <p className="text-xs text-gray-500 mt-1">Fuentes de datos</p>
            </div>
            <div>
              <p className="text-3xl font-extrabold text-gray-900">24/7</p>
              <p className="text-xs text-gray-500 mt-1">Monitoreo activo</p>
            </div>
            <div>
              <p className="text-3xl font-extrabold text-gray-900">2 min</p>
              <p className="text-xs text-gray-500 mt-1">Para configurar</p>
            </div>
          </div>
        </div>
      </section>

      {/* Data sources — scrolling marquee */}
      <section id="sources" className="border-y border-gray-100 bg-white py-12 overflow-hidden">
        <p className="text-center text-sm font-semibold text-gray-400 uppercase tracking-wider mb-8">Fuentes que monitoreamos para ti</p>
        <div className="relative">
          <div className="absolute left-0 top-0 h-full w-24 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none" />
          <div className="absolute right-0 top-0 h-full w-24 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none" />
          <div className="flex animate-marquee whitespace-nowrap select-none" aria-hidden>
            {[...SOURCES, ...SOURCES].map((s, i) => (
              <div key={i} className="inline-flex flex-col items-center mx-8 min-w-max">
                <span className="text-base font-semibold text-gray-800">{s.name}</span>
                <span className="text-xs text-gray-400 mt-0.5">{s.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Highlight Banner */}
      <section className="bg-gradient-to-r from-purple-600 to-brand-600 py-12">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 bg-white/20 text-white text-sm font-medium px-4 py-1.5 rounded-full mb-4">
            <Sparkles className="h-4 w-4" /> Nuevo — Inteligencia Artificial
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white">
            Cada mañana, la IA analiza todos los contratos y te dice cuáles ganar
          </h2>
          <p className="mt-3 text-purple-100 max-w-xl mx-auto">
            No filtramos. Analizamos. Comparamos tu perfil contra cada contrato y te entregamos un ranking personalizado con razonamiento. Coste real: &lt;$0.001 por usuario al día.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-4 text-sm text-purple-100">
            <span className="flex items-center gap-1.5"><Trophy className="h-4 w-4 text-yellow-300" /> Ranking diario personalizado</span>
            <span className="flex items-center gap-1.5"><Brain className="h-4 w-4 text-purple-200" /> Análisis por contrato bajo demanda</span>
            <span className="flex items-center gap-1.5"><Check className="h-4 w-4 text-green-300" /> Caché 24h — prácticamente gratis</span>
          </div>
          <Link to="/login" className="inline-block mt-8">
            <Button size="lg" className="bg-white !text-purple-700 hover:bg-purple-50 shadow-lg">
              Probar gratis <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <p className="text-sm font-semibold text-brand-600 uppercase tracking-wider mb-3">Funciones</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">Todo lo que necesitas para ganar más contratos</h2>
          <p className="mt-4 text-gray-500 max-w-xl mx-auto">De la búsqueda al cierre. IA que trabaja mientras duermes. Sin herramientas sueltas, sin Excel, sin perder oportunidades.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <div key={f.title} className="group p-6 rounded-2xl border border-gray-100 hover:border-brand-200 hover:shadow-lg hover:shadow-brand-50/80 transition-all duration-300">
              <div className={`inline-flex h-12 w-12 rounded-xl ${f.color.split(" ")[0]} items-center justify-center transition-colors`}>
                <f.icon className={`h-6 w-6 ${f.color.split(" ")[1]}`} />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900">{f.title}</h3>
              <p className="mt-2 text-sm text-gray-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold text-brand-600 uppercase tracking-wider mb-3">Cómo funciona</p>
            <h2 className="text-3xl font-bold text-gray-900">4 pasos para empezar a ganar</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {[
              { step: "1", title: "Configura tu perfil", desc: "Sector, ciudad y qué contratos buscas. Menos de 2 minutos. La IA lo usa para todo lo demás." },
              { step: "2", title: "Recibe recomendaciones", desc: "Cada día la IA analiza todos los contratos y te entrega los mejores con explicación de por qué." },
              { step: "3", title: "Analiza y decide", desc: "Abre un contrato, pide análisis IA: complejidad, competencia, requisitos, probabilidad de ganar." },
              { step: "4", title: "Gestiona y cierra", desc: "Pipeline CRM para seguimiento, Marketplace para conectar con proveedores y alertas para no perderte nada." },
            ].map((s) => (
              <div key={s.step} className="text-center">
                <div className="mx-auto h-14 w-14 rounded-2xl bg-brand-600 text-white flex items-center justify-center text-xl font-bold mb-4">
                  {s.step}
                </div>
                <h3 className="text-base font-semibold text-gray-900">{s.title}</h3>
                <p className="mt-2 text-sm text-gray-500 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Live Demo — Real Contracts */}
      <section id="demo" className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-sm font-semibold text-brand-600 uppercase tracking-wider mb-3">Demo en vivo</p>
            <h2 className="text-3xl font-bold text-gray-900">Contratos reales publicados hoy</h2>
            <p className="mt-4 text-gray-500 max-w-xl mx-auto">Estos son contratos activos. Crea tu cuenta gratis para ver más, recibir alertas y obtener recomendaciones IA.</p>
          </div>
          {demoStats && (
            <div className="flex flex-wrap items-center justify-center gap-8 mb-10">
              <div className="text-center">
                <p className="text-3xl font-bold text-gray-900">{(demoStats.total_contracts || 0).toLocaleString("es-CO")}</p>
                <p className="text-xs text-gray-500 mt-1">Contratos totales</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-brand-600">{demoStats.today_new || 0}+</p>
                <p className="text-xs text-gray-500 mt-1">Nuevos hoy</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-gray-900">{Object.keys(demoStats.sources || {}).length || 12}</p>
                <p className="text-xs text-gray-500 mt-1">Fuentes activas</p>
              </div>
            </div>
          )}
          {loadingDemo ? (
            <div className="flex justify-center py-12"><Spinner /></div>
          ) : demoContracts.length === 0 ? (
            <p className="text-center text-gray-500">No hay contratos disponibles en este momento.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {demoContracts.map((c) => (
                <div key={c.id} className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-lg hover:border-brand-200 transition-all group">
                  <div className="flex items-start gap-3 mb-3">
                    <div className="flex-shrink-0 h-10 w-10 rounded-lg bg-brand-50 flex items-center justify-center">
                      <FileText className="h-5 w-5 text-brand-600" />
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 group-hover:text-brand-700 transition">{c.title}</h3>
                  </div>
                  <div className="space-y-2 text-xs text-gray-500">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-3.5 w-3.5" />
                      <span className="truncate">{c.entity || "Entidad no especificada"}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>Cierra: {formatDate(c.deadline)}</span>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
                    <span className="text-sm font-bold text-gray-900">{formatMoney(c.amount)}</span>
                    <span className="text-xs text-gray-400 uppercase">{c.source || "SECOP"}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="mt-10 text-center">
            <Link to="/login">
              <Button size="lg">
                <Search className="h-5 w-5" /> Ver todos los contratos
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-20 bg-gray-50">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-sm font-semibold text-brand-600 uppercase tracking-wider mb-3">Testimonios</p>
            <h2 className="text-3xl font-bold text-gray-900">Profesionales colombianos que ya están ganando</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((t) => (
              <div key={t.name} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition">
                <div className="flex gap-1 mb-4">
                  {[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-brand-400 text-brand-400" />)}
                </div>
                <p className="text-sm text-gray-600 leading-relaxed">&ldquo;{t.text}&rdquo;</p>
                <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center text-white text-xs font-bold">
                    {t.avatar}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{t.name}</p>
                    <p className="text-xs text-gray-500">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="bg-white py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-sm font-semibold text-brand-600 uppercase tracking-wider mb-3">Precios en COP</p>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">Invierte menos de lo que pierdes en una licitación</h2>
            <p className="mt-4 text-gray-500">Empieza gratis. Actualiza cuando quieras. IVA incluido. Cancela en cualquier momento.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {PLANS.map((plan) => (
              <div key={plan.name} className={`bg-white rounded-2xl p-5 border-2 transition-all duration-300 hover:shadow-lg flex flex-col ${plan.popular ? "border-brand-500 shadow-lg shadow-brand-100 scale-[1.02]" : "border-gray-100 hover:border-gray-200"}`}>
                {plan.popular && (
                  <span className="inline-block text-xs font-bold text-white bg-brand-600 px-3 py-1 rounded-full mb-3 self-start">MÁS POPULAR</span>
                )}
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{plan.emoji}</span>
                  <h3 className="text-base font-bold text-gray-900">{plan.name}</h3>
                </div>
                <p className="mb-4">
                  <span className="text-2xl font-extrabold text-gray-900">{plan.price}</span>
                  {plan.price !== "Gratis" && <span className="text-xs text-gray-500">/mes</span>}
                </p>
                <ul className="space-y-1.5 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-xs text-gray-600">
                      <Check className="h-3.5 w-3.5 text-accent-500 flex-shrink-0 mt-0.5" /> {f}
                    </li>
                  ))}
                </ul>
                <Link to="/login" className="block mt-5">
                  <Button className="w-full" size="sm" variant={plan.popular ? "primary" : "secondary"}>
                    {plan.price === "Gratis" ? "Crear cuenta" : "Empezar gratis"}
                  </Button>
                </Link>
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-gray-400 mt-6">Todos los planes incluyen acceso a todos los contratos. La diferencia está en las funciones y la IA.</p>
        </div>
      </section>

      {/* Security callout */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-4xl mx-auto px-6">
          <div className="rounded-2xl border border-gray-200 bg-white p-8 md:p-12 flex flex-col md:flex-row items-center gap-8">
            <div className="flex-shrink-0">
              <div className="h-20 w-20 rounded-2xl bg-accent-50 flex items-center justify-center">
                <Shield className="h-10 w-10 text-accent-600" />
              </div>
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">Tus datos están protegidos</h3>
              <p className="mt-2 text-sm text-gray-500 leading-relaxed">
                Auth sin contraseñas (magic links), tokens JWT con rotación automática, validación contra SQL injection y XSS,
                rate limiting por IP, verificación HMAC en pagos, auditoría completa de acciones sensibles.
                Cumplimos con la <strong>Ley 1581 de 2012</strong> de protección de datos de Colombia.
              </p>
              <div className="mt-4 flex gap-4">
                <Link to="/privacy" className="text-sm text-brand-600 hover:text-brand-700 font-medium transition">Ver política de privacidad</Link>
                <Link to="/terms" className="text-sm text-gray-500 hover:text-gray-700 font-medium transition">Términos de uso</Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gray-900 py-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-900/20 to-accent-900/20" />
        <div className="max-w-3xl mx-auto px-6 text-center relative">
          <Logo size={56} className="mx-auto mb-6" />
          <h2 className="text-3xl sm:text-4xl font-bold text-white">¿Cuántos contratos estás perdiendo por no buscar bien?</h2>
          <p className="mt-4 text-gray-400 max-w-xl mx-auto">Configura tu perfil en 2 minutos. La IA empieza a trabajar por ti desde el primer día.</p>
          <div className="mt-8 flex flex-col sm:flex-row justify-center gap-4">
            <Link to="/login">
              <Button size="lg" className="bg-white !text-gray-900 hover:bg-gray-100 shadow-lg">
                Crear cuenta gratis <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-950 text-gray-400">
        <div className="max-w-6xl mx-auto px-6 py-10">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Logo size={24} />
              <span className="font-semibold text-white">Jobper</span>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <Link to="/terms" className="hover:text-white transition">Términos</Link>
              <Link to="/privacy" className="hover:text-white transition">Privacidad</Link>
              <span>soporte@jobper.co</span>
            </div>
            <p className="text-sm">Jobper &copy; {new Date().getFullYear()} — Hecho en Colombia</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
