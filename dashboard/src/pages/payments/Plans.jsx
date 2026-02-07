import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useApi } from "../../hooks/useApi";
import { api } from "../../lib/api";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import Modal from "../../components/ui/Modal";
import { money, date } from "../../lib/format";
import { useToast } from "../../components/ui/Toast";
import {
  Check,
  X,
  Zap,
  Copy,
  Shield,
  Banknote,
  ChevronRight,
  Upload,
  ImageIcon,
  Eye,
  Target,
  Sword,
  Crown,
  Lock,
  Sparkles,
  TrendingUp,
  Users,
  Bot,
  FileText,
  Bell,
  Star,
  RefreshCw,
} from "lucide-react";
import { TrustBadge, TrustCard } from "../../components/ui/TrustBadge";

// =============================================================================
// LOS 4 PLANES DE JOBPER — Diferenciación brutal
// =============================================================================
const PLANS = [
  {
    key: "free",
    name: "Gratis",
    displayName: "Observador",
    price: 0,
    emoji: "👀",
    icon: Eye,
    color: "gray",
    tagline: "Descubre oportunidades",
    features: [
      { text: "Ver todos los contratos públicos", included: true },
      { text: "10 búsquedas por día", included: true },
      { text: "10 favoritos máximo", included: true },
      { text: "Descripción completa", included: false },
      { text: "Match score de compatibilidad", included: false },
      { text: "Ver montos de contratos", included: false },
      { text: "Alertas por email", included: false },
    ],
  },
  {
    key: "cazador",
    name: "Cazador",
    displayName: "Cazador",
    price: 29900,
    emoji: "🎯",
    icon: Target,
    color: "blue",
    tagline: "Encuentra antes que otros",
    features: [
      { text: "Búsquedas ilimitadas", included: true },
      { text: "Descripciones completas", included: true, highlight: true },
      { text: "Match score real (%)", included: true, highlight: true },
      { text: "Ver montos de contratos", included: true, highlight: true },
      { text: "50 alertas/semana por email", included: true },
      { text: "100 favoritos", included: true },
      { text: "Exportar 50/mes a Excel", included: true },
      { text: "Contratos privados", included: false },
      { text: "Análisis IA", included: false },
    ],
  },
  {
    key: "competidor",
    name: "Competidor",
    displayName: "Competidor",
    price: 149900,
    emoji: "⚔️",
    icon: Sword,
    color: "purple",
    tagline: "Gana más contratos",
    popular: true,
    features: [
      { text: "Todo de Cazador +", included: true },
      { text: "Contratos PRIVADOS", included: true, highlight: true },
      { text: "Alertas instantáneas (push)", included: true, highlight: true },
      { text: "Análisis IA por contrato", included: true, highlight: true },
      { text: "Pipeline CRM de ventas", included: true },
      { text: "Favoritos ilimitados", included: true },
      { text: "Exportar 500/mes", included: true },
      { text: "Historial 1 año", included: true },
      { text: "Inteligencia competitiva", included: false },
    ],
  },
  {
    key: "dominador",
    name: "Dominador",
    displayName: "Dominador",
    price: 599900,
    emoji: "👑",
    icon: Crown,
    color: "amber",
    tagline: "Domina tu sector",
    features: [
      { text: "Todo de Competidor +", included: true },
      { text: "Inteligencia competitiva", included: true, highlight: true },
      { text: "5 usuarios incluidos", included: true, highlight: true },
      { text: "Auto-propuestas con IA", included: true, highlight: true },
      { text: "Red de consorcios", included: true },
      { text: "API access", included: true },
      { text: "Soporte WhatsApp 4h", included: true },
      { text: "Consultoría mensual 1h", included: true },
      { text: "Reportes personalizados", included: true },
    ],
  },
];

// Plan key aliases for backwards compatibility
const PLAN_ALIASES = {
  alertas: "cazador",
  business: "competidor",
  enterprise: "dominador",
  starter: "cazador",
  trial: "free",
};

function normalizePlan(plan) {
  return PLAN_ALIASES[plan] || plan || "free";
}

export default function Plans() {
  const { user, refresh } = useAuth();
  const { data: sub, loading } = useApi("/payments/subscription");
  const { data: trustInfo, loading: loadingTrust, refresh: refreshTrust } = useApi("/payments/trust");
  const toast = useToast();
  const [searchParams] = useSearchParams();
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [showPayment, setShowPayment] = useState(false);
  const [checkout, setCheckout] = useState(null);
  const [loadingCheckout, setLoadingCheckout] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [comprobante, setComprobante] = useState(null);
  const [comprobantePreview, setComprobantePreview] = useState(null);
  const [renewalLoading, setRenewalLoading] = useState(false);

  // Auto-open modal if plan param in URL
  useEffect(() => {
    const planParam = searchParams.get("plan");
    if (planParam) {
      const normalized = normalizePlan(planParam);
      const plan = PLANS.find((p) => p.key === normalized);
      if (plan && plan.price > 0) {
        openPaymentModal(plan);
      }
    }
  }, [searchParams]);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copiado");
  };

  const openPaymentModal = async (plan) => {
    setSelectedPlan(plan);
    setShowPayment(true);
    setLoadingCheckout(true);
    try {
      const data = await api.post("/payments/checkout", { plan: plan.key });
      setCheckout(data);
    } catch (err) {
      toast.error(err.error || "Error cargando información de pago");
      setShowPayment(false);
      setSelectedPlan(null);
    } finally {
      setLoadingCheckout(false);
    }
  };

  const handleComprobanteChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (!allowed.includes(file.type)) {
      toast.error("Solo se permiten imágenes (JPG, PNG, WebP)");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error("El archivo no puede superar 5MB");
      return;
    }

    setComprobante(file);
    setComprobantePreview(URL.createObjectURL(file));
  };

  const confirmPayment = async () => {
    if (!comprobante || !checkout?.payment_id) return;

    setConfirming(true);
    try {
      const formData = new FormData();
      formData.append("payment_id", checkout.payment_id);
      formData.append("comprobante", comprobante);

      const result = await api.upload("/payments/confirm", formData);

      // Handle different verification statuses
      if (result.status === "approved" || result.ok) {
        toast.success(`¡Plan ${result.plan} activado! Disfruta Jobper.`);

        // Show trust rewards if any were earned
        if (result.rewards && result.rewards.length > 0) {
          result.rewards.forEach((reward) => {
            setTimeout(() => {
              toast.success(reward.message);
            }, 1500);
          });
        } else if (result.trust?.points_earned) {
          setTimeout(() => {
            toast.info(`+${result.trust.points_earned} puntos de confianza`);
          }, 1500);
        }

        await refresh();
        refreshTrust();  // Refresh trust info to show new badge
        setShowPayment(false);
        setSelectedPlan(null);
        setCheckout(null);
        setComprobante(null);
        setComprobantePreview(null);
      } else if (result.status === "review") {
        toast.info(result.message || "Tu comprobante está siendo verificado. Te notificaremos pronto.");
        setShowPayment(false);
        setSelectedPlan(null);
        setCheckout(null);
        setComprobante(null);
        setComprobantePreview(null);
      } else if (result.status === "rejected") {
        const issues = result.issues?.join(", ") || result.message || "Comprobante no válido";
        toast.error(`Verificación fallida: ${issues}. Puedes intentar de nuevo.`);
        // Don't close modal, allow retry
        setComprobante(null);
        setComprobantePreview(null);
      }
    } catch (err) {
      // Handle HTTP error responses
      if (err.status === "review") {
        toast.info(err.message || "Tu comprobante está siendo revisado manualmente.");
        setShowPayment(false);
      } else if (err.status === "rejected" && err.can_retry) {
        const issues = err.issues?.join(", ") || "Comprobante no válido";
        toast.error(`${issues}. Puedes intentar con otro comprobante.`);
        setComprobante(null);
        setComprobantePreview(null);
      } else {
        toast.error(err.error || err.message || "Error confirmando pago");
      }
    } finally {
      setConfirming(false);
    }
  };

  const cancel = async () => {
    if (!confirm("¿Seguro que quieres cancelar tu suscripción?")) return;
    try {
      await api.post("/payments/cancel");
      toast.success("Suscripción cancelada");
      refresh();
    } catch (err) {
      toast.error(err.error || "Error cancelando");
    }
  };

  // One-click renewal for trusted payers
  const handleOneClickRenewal = async () => {
    setRenewalLoading(true);
    try {
      const result = await api.post("/payments/one-click-renewal", {});
      if (result.ok) {
        setCheckout(result);
        setSelectedPlan(PLANS.find((p) => p.key === result.plan) || PLANS[1]);
        setShowPayment(true);
        toast.info("Transferencia preparada. Solo sube tu comprobante.");
      }
    } catch (err) {
      toast.error(err.error || "Error iniciando renovación");
    } finally {
      setRenewalLoading(false);
    }
  };

  if (loading)
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    );

  const nequi = checkout?.payment_methods?.nequi;
  const banco = checkout?.payment_methods?.bancolombia;
  const userPlan = normalizePlan(user?.plan);

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Elige tu plan</h1>
        <p className="text-gray-500 mt-2">
          Desbloquea todo el poder de Jobper para encontrar y ganar contratos
        </p>
      </div>

      {/* Current subscription banner */}
      {sub?.subscription && (
        <Card className="bg-gradient-to-r from-brand-50 to-brand-100 border-brand-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-brand-200 rounded-full">
                <Sparkles className="h-5 w-5 text-brand-700" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-brand-800">
                    Plan {sub.subscription.plan} activo
                  </p>
                  <TrustBadge level={trustInfo?.trust_level} size="sm" />
                </div>
                <p className="text-sm text-brand-600">
                  Hasta {date(sub.subscription.ends_at)}
                  {sub.subscription.days_remaining <= 5 && (
                    <span className="ml-2 text-red-600 font-medium">
                      (¡Vence en {sub.subscription.days_remaining} días!)
                    </span>
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {trustInfo?.one_click_renewal_enabled && sub.subscription.days_remaining <= 7 && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleOneClickRenewal}
                  disabled={renewalLoading}
                >
                  {renewalLoading ? (
                    <Spinner className="h-4 w-4" />
                  ) : (
                    <>
                      <RefreshCw className="h-4 w-4 mr-1" />
                      Renovar 1-clic
                    </>
                  )}
                </Button>
              )}
              <Button variant="secondary" size="sm" onClick={cancel}>
                Cancelar
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Trust Card for verified payers */}
      {trustInfo && trustInfo.verified_payments_count >= 1 && (
        <TrustCard trustInfo={trustInfo} />
      )}

      {/* Feature highlight from URL */}
      {searchParams.get("feature") && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center gap-3">
          <Lock className="h-5 w-5 text-blue-600" />
          <p className="text-blue-800">
            <strong>
              {searchParams.get("feature").replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
            </strong>{" "}
            está disponible en los planes de pago. Elige uno para desbloquear.
          </p>
        </div>
      )}

      {/* Plans grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {PLANS.map((plan) => {
          const Icon = plan.icon;
          const isCurrent = userPlan === plan.key;
          const isDowngrade =
            PLANS.findIndex((p) => p.key === userPlan) > PLANS.findIndex((p) => p.key === plan.key);

          return (
            <Card
              key={plan.key}
              className={`relative flex flex-col ${
                plan.popular ? "ring-2 ring-purple-500 shadow-lg" : ""
              } ${plan.color === "amber" ? "bg-gradient-to-b from-amber-50 to-white" : ""}`}
            >
              {/* Popular badge */}
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge color="purple" className="shadow-md">
                    <Zap className="h-3 w-3 mr-1" /> Más popular
                  </Badge>
                </div>
              )}

              <div className="flex-1 space-y-4">
                {/* Header */}
                <div className="text-center pt-2">
                  <div
                    className={`inline-flex items-center justify-center w-12 h-12 rounded-full mb-3 ${
                      plan.color === "gray" ? "bg-gray-100" : ""
                    } ${plan.color === "blue" ? "bg-blue-100" : ""} ${
                      plan.color === "purple" ? "bg-purple-100" : ""
                    } ${plan.color === "amber" ? "bg-amber-100" : ""}`}
                  >
                    <Icon
                      className={`h-6 w-6 ${plan.color === "gray" ? "text-gray-600" : ""} ${
                        plan.color === "blue" ? "text-blue-600" : ""
                      } ${plan.color === "purple" ? "text-purple-600" : ""} ${
                        plan.color === "amber" ? "text-amber-600" : ""
                      }`}
                    />
                  </div>
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-2xl">{plan.emoji}</span>
                    <h3 className="text-xl font-bold text-gray-900">{plan.displayName}</h3>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{plan.tagline}</p>
                </div>

                {/* Price */}
                <div className="text-center py-2">
                  {plan.price === 0 ? (
                    <p className="text-3xl font-bold text-gray-900">Gratis</p>
                  ) : (
                    <div>
                      <p className="text-3xl font-bold text-gray-900">
                        {money(plan.price)}
                        <span className="text-base font-normal text-gray-500">/mes</span>
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {money(plan.price * 12)}/año
                      </p>
                    </div>
                  )}
                </div>

                {/* Features */}
                <ul className="space-y-2.5 px-2">
                  {plan.features.map((f, i) => (
                    <li
                      key={i}
                      className={`flex items-start gap-2 text-sm ${
                        f.included ? "text-gray-700" : "text-gray-400"
                      }`}
                    >
                      {f.included ? (
                        <Check
                          className={`h-4 w-4 flex-shrink-0 mt-0.5 ${
                            f.highlight ? "text-green-500" : "text-green-400"
                          }`}
                        />
                      ) : (
                        <X className="h-4 w-4 flex-shrink-0 mt-0.5 text-gray-300" />
                      )}
                      <span className={f.highlight ? "font-medium" : ""}>{f.text}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* CTA Button */}
              <div className="pt-4 mt-4 border-t border-gray-100">
                {isCurrent ? (
                  <Button className="w-full" variant="secondary" disabled>
                    <Check className="h-4 w-4 mr-1" /> Plan actual
                  </Button>
                ) : plan.price === 0 ? (
                  <Button className="w-full" variant="secondary" disabled>
                    Plan gratuito
                  </Button>
                ) : isDowngrade ? (
                  <Button className="w-full" variant="secondary" disabled>
                    Ya tienes un plan superior
                  </Button>
                ) : (
                  <Button
                    className={`w-full ${
                      plan.color === "blue" ? "bg-blue-600 hover:bg-blue-700" : ""
                    } ${plan.color === "purple" ? "bg-purple-600 hover:bg-purple-700" : ""} ${
                      plan.color === "amber" ? "bg-amber-600 hover:bg-amber-700" : ""
                    }`}
                    onClick={() => openPaymentModal(plan)}
                  >
                    Activar {plan.displayName}
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Trust badges */}
      <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-gray-500">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-green-500" />
          <span>Pago seguro por transferencia</span>
        </div>
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-yellow-500" />
          <span>Activación inmediata</span>
        </div>
        <div className="flex items-center gap-2">
          <X className="h-4 w-4 text-gray-400" />
          <span>Cancela cuando quieras</span>
        </div>
      </div>

      {/* Comparison table for larger screens */}
      <div className="hidden lg:block mt-12">
        <h2 className="text-xl font-bold text-gray-900 text-center mb-6">
          Comparación detallada
        </h2>
        <ComparisonTable plans={PLANS} currentPlan={userPlan} />
      </div>

      {/* Payment Modal */}
      {showPayment && selectedPlan && (
        <Modal
          open={true}
          onClose={() => {
            setShowPayment(false);
            setSelectedPlan(null);
            setCheckout(null);
            setComprobante(null);
            setComprobantePreview(null);
          }}
        >
          <div className="space-y-5">
            <div className="text-center">
              <div
                className={`inline-flex items-center justify-center w-14 h-14 rounded-full mb-3 ${
                  selectedPlan.color === "blue" ? "bg-blue-100" : ""
                } ${selectedPlan.color === "purple" ? "bg-purple-100" : ""} ${
                  selectedPlan.color === "amber" ? "bg-amber-100" : ""
                }`}
              >
                <span className="text-3xl">{selectedPlan.emoji}</span>
              </div>
              <h2 className="text-xl font-bold text-gray-900">
                Activar {selectedPlan.displayName}
              </h2>
              <p className="text-2xl font-bold text-brand-600 mt-1">
                {checkout?.amount_display || money(selectedPlan.price) + " COP"}
                <span className="text-sm font-normal text-gray-500">/mes</span>
              </p>
            </div>

            {loadingCheckout ? (
              <div className="flex justify-center py-6">
                <Spinner />
              </div>
            ) : checkout ? (
              <div className="space-y-4">
                <p className="text-sm text-gray-600 text-center">{checkout.instructions}</p>

                {checkout.reference && (
                  <div className="bg-amber-50 border-2 border-amber-300 rounded-lg p-4 text-center">
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <span className="text-lg">⚠️</span>
                      <p className="text-sm font-bold text-amber-800">IMPORTANTE: Incluye este código</p>
                    </div>
                    <div className="bg-white border border-amber-200 rounded-lg p-3 mb-2">
                      <div className="flex items-center justify-center gap-2">
                        <p className="text-lg font-mono font-bold text-gray-900 tracking-wide">
                          {checkout.reference}
                        </p>
                        <button
                          onClick={() => copyToClipboard(checkout.reference)}
                          className="p-2 hover:bg-amber-100 rounded-lg transition"
                          title="Copiar referencia"
                        >
                          <Copy className="h-4 w-4 text-amber-600" />
                        </button>
                      </div>
                    </div>
                    <p className="text-xs text-amber-700">
                      Copia este código y pégalo en la <strong>descripción/concepto</strong> de tu transferencia.
                      <br />
                      Sin el código, no podremos verificar tu pago automáticamente.
                    </p>
                  </div>
                )}

                {/* Nequi */}
                {nequi?.number && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-purple-600 font-semibold uppercase tracking-wide">
                          {nequi.name}
                        </p>
                        <p className="text-lg text-purple-800 font-mono font-bold mt-1">
                          {nequi.number}
                        </p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(nequi.number)}
                        className="p-2 hover:bg-purple-100 rounded-lg transition"
                      >
                        <Copy className="h-4 w-4 text-purple-600" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Bancolombia */}
                {banco?.account && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-xs text-yellow-600 font-semibold uppercase tracking-wide">
                      {banco.name} — {banco.type}
                    </p>
                    <div className="flex items-center justify-between mt-1">
                      <div>
                        <p className="text-lg text-yellow-800 font-mono font-bold">
                          {banco.account}
                        </p>
                        <p className="text-xs text-yellow-700 mt-0.5">{banco.holder}</p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(banco.account)}
                        className="p-2 hover:bg-yellow-100 rounded-lg transition"
                      >
                        <Copy className="h-4 w-4 text-yellow-600" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Comprobante upload */}
                <div className="border-t border-gray-200 pt-4 space-y-3">
                  <p className="text-sm font-medium text-gray-700">
                    ¿Ya transferiste? Sube tu comprobante:
                  </p>

                  <label className="flex items-center justify-center gap-2 w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer hover:border-brand-400 hover:bg-brand-50/50 transition">
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="hidden"
                      onChange={handleComprobanteChange}
                    />
                    {comprobantePreview ? (
                      <div className="flex items-center gap-3 w-full">
                        <img
                          src={comprobantePreview}
                          alt="Comprobante"
                          className="h-12 w-12 object-cover rounded-lg"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-800 truncate">
                            {comprobante?.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {(comprobante?.size / 1024).toFixed(0)} KB — Toca para cambiar
                          </p>
                        </div>
                        <ImageIcon className="h-4 w-4 text-green-500" />
                      </div>
                    ) : (
                      <>
                        <Upload className="h-5 w-5 text-gray-400" />
                        <span className="text-sm text-gray-500">
                          Seleccionar imagen del comprobante
                        </span>
                      </>
                    )}
                  </label>

                  <Button
                    className="w-full h-12 text-base"
                    onClick={confirmPayment}
                    disabled={!comprobante || confirming}
                  >
                    {confirming ? (
                      <>
                        <Spinner className="h-5 w-5 mr-2" />
                        Verificando comprobante...
                      </>
                    ) : (
                      <>
                        Verificar y activar plan <ChevronRight className="h-4 w-4" />
                      </>
                    )}
                  </Button>
                  <p className="text-xs text-center text-gray-400">
                    Verificamos tu comprobante con IA. Si todo está correcto, tu plan se activa al instante.
                  </p>
                </div>
              </div>
            ) : null}
          </div>
        </Modal>
      )}
    </div>
  );
}

// =============================================================================
// COMPARISON TABLE COMPONENT
// =============================================================================
function ComparisonTable({ plans, currentPlan }) {
  const features = [
    { key: "searches", label: "Búsquedas/día", values: ["10", "∞", "∞", "∞"] },
    { key: "favorites", label: "Favoritos", values: ["10", "100", "∞", "∞"] },
    { key: "alerts", label: "Alertas/semana", values: ["—", "50", "∞", "∞"] },
    { key: "description", label: "Descripción completa", values: [false, true, true, true] },
    { key: "score", label: "Match score", values: [false, true, true, true] },
    { key: "amount", label: "Ver montos", values: [false, true, true, true] },
    { key: "export", label: "Exportar/mes", values: ["—", "50", "500", "∞"] },
    { key: "private", label: "Contratos privados", values: [false, false, true, true] },
    { key: "ai", label: "Análisis IA", values: [false, false, true, true] },
    { key: "pipeline", label: "Pipeline CRM", values: [false, false, true, true] },
    { key: "push", label: "Alertas push", values: [false, false, true, true] },
    { key: "intel", label: "Inteligencia competitiva", values: [false, false, false, true] },
    { key: "team", label: "Multi-usuario", values: ["1", "1", "1", "5"] },
    { key: "api", label: "API access", values: [false, false, false, true] },
    { key: "support", label: "Soporte", values: ["—", "Email 48h", "Email 24h", "WhatsApp 4h"] },
  ];

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="text-left p-3 border-b border-gray-200"></th>
            {plans.map((plan) => (
              <th
                key={plan.key}
                className={`text-center p-3 border-b border-gray-200 ${
                  plan.popular ? "bg-purple-50" : ""
                }`}
              >
                <div className="flex flex-col items-center gap-1">
                  <span className="text-xl">{plan.emoji}</span>
                  <span className="font-bold">{plan.displayName}</span>
                  <span className="text-sm text-gray-500">
                    {plan.price === 0 ? "Gratis" : money(plan.price)}
                  </span>
                  {currentPlan === plan.key && (
                    <Badge color="green" className="mt-1">
                      Actual
                    </Badge>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {features.map((f) => (
            <tr key={f.key} className="hover:bg-gray-50">
              <td className="p-3 border-b border-gray-100 text-sm font-medium text-gray-700">
                {f.label}
              </td>
              {f.values.map((v, i) => (
                <td
                  key={i}
                  className={`text-center p-3 border-b border-gray-100 ${
                    plans[i].popular ? "bg-purple-50/50" : ""
                  }`}
                >
                  {typeof v === "boolean" ? (
                    v ? (
                      <Check className="h-5 w-5 text-green-500 mx-auto" />
                    ) : (
                      <X className="h-5 w-5 text-gray-300 mx-auto" />
                    )
                  ) : (
                    <span className="text-sm text-gray-600">{v}</span>
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
