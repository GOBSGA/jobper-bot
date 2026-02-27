import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useApi } from "../../hooks/useApi";
import { api } from "../../lib/api";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { money, date } from "../../lib/format";
import { useToast } from "../../components/ui/Toast";
import { normalizePlan } from "../../lib/planConfig";
import GraceBanner from "../../components/payments/GraceBanner";
import PlanCard from "../../components/payments/PlanCard";
import PaymentModal from "../../components/payments/PaymentModal";
import {
  Check,
  X,
  Lightning,
  ShieldCheck,
  Eye,
  Target,
  Sword,
  Crown,
  Lock,
  Sparkle,
  ArrowsClockwise,
  Clock,
} from "@phosphor-icons/react";
import { TrustBadge, TrustCard } from "../../components/ui/TrustBadge";

// =============================================================================
// PLANES DE JOBPER
// =============================================================================
const PLANS = [
  {
    key: "free",
    name: "Gratis",
    displayName: "Observador",
    price: 0,
    emoji: "👀",
    icon: Eye,
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
    key: "estratega",
    name: "Estratega",
    displayName: "Estratega",
    price: 299900,
    emoji: "🚀",
    icon: Lightning,
    tagline: "Escala tu equipo",
    features: [
      { text: "Todo de Competidor +", included: true },
      { text: "2 usuarios en equipo", included: true, highlight: true },
      { text: "Historial 2 años", included: true, highlight: true },
      { text: "Reportes automáticos mensuales", included: true, highlight: true },
      { text: "Exportar ilimitado", included: true },
      { text: "Soporte email prioritario 12h", included: true },
      { text: "Inteligencia competitiva", included: false },
      { text: "Auto-propuestas IA", included: false },
    ],
  },
  {
    key: "dominador",
    name: "Dominador",
    displayName: "Dominador",
    price: 599900,
    emoji: "👑",
    icon: Crown,
    tagline: "Domina tu sector",
    features: [
      { text: "Todo de Estratega +", included: true },
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

export default function Plans() {
  const { user, refresh } = useAuth();
  const { data: sub, loading, error: subError, refetch: refetchSub } = useApi("/payments/subscription");
  const { data: trustInfo, refetch: refreshTrust } = useApi("/payments/trust");
  const { data: paymentStatus } = useApi("/payments/status");
  const toast = useToast();
  const [searchParams] = useSearchParams();
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [checkout, setCheckout] = useState(null);
  const [loadingCheckout, setLoadingCheckout] = useState(false);
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

  const openPaymentModal = async (plan) => {
    setSelectedPlan(plan);
    setLoadingCheckout(true);
    try {
      const data = await api.post("/payments/checkout", { plan: plan.key });
      setCheckout(data);
    } catch (err) {
      toast.error(err.error || "Error cargando información de pago");
      setSelectedPlan(null);
    } finally {
      setLoadingCheckout(false);
    }
  };

  const closePaymentModal = () => {
    setSelectedPlan(null);
    setCheckout(null);
  };

  const handlePaymentSuccess = async () => {
    await refresh();
    refreshTrust();
    closePaymentModal();
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

  const handleOneClickRenewal = async () => {
    setRenewalLoading(true);
    try {
      const result = await api.post("/payments/one-click-renewal", {});
      if (result.ok) {
        setCheckout(result);
        setSelectedPlan(PLANS.find((p) => p.key === result.plan) || PLANS[1]);
        toast.info("Transferencia preparada. Solo sube tu comprobante.");
      }
    } catch (err) {
      toast.error(err.error || "Error iniciando renovación");
    } finally {
      setRenewalLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    );
  }

  const userPlan = normalizePlan(user?.plan);

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-ink-900 tracking-snug">Elige tu plan</h1>
        <p className="text-sm text-ink-400 mt-2">
          Desbloquea todo el poder de Jobper para encontrar y ganar contratos
        </p>
      </div>

      {/* Subscription load error */}
      {subError && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-800 flex items-center justify-between gap-3">
          <span>No se pudo cargar tu suscripción actual.</span>
          <button
            onClick={refetchSub}
            className="px-3 py-1 rounded-lg bg-amber-100 hover:bg-amber-200 text-amber-800 font-medium text-xs transition"
          >
            Reintentar
          </button>
        </div>
      )}

      {/* Current subscription banner */}
      {sub?.subscription && (
        <Card className="bg-brand-50 border-brand-200 p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-brand-100 flex items-center justify-center flex-shrink-0">
                <Sparkle size={17} weight="duotone" className="text-brand-600" />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-sm font-semibold text-brand-800">
                    Plan {sub.subscription.plan} activo
                  </p>
                  <TrustBadge level={trustInfo?.trust_level} size="sm" />
                </div>
                <p className="text-xs text-brand-600 mt-0.5">
                  Hasta {date(sub.subscription.ends_at)}
                  {sub.subscription.days_remaining <= 5 && (
                    <span className="ml-2 text-red-600 font-medium">
                      (vence en {sub.subscription.days_remaining} días)
                    </span>
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {trustInfo?.one_click_renewal_enabled && sub.subscription.days_remaining <= 7 && (
                <Button size="sm" onClick={handleOneClickRenewal} disabled={renewalLoading}>
                  {renewalLoading ? (
                    <Spinner />
                  ) : (
                    <>
                      <ArrowsClockwise size={13} />
                      Renovar
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

      {/* Grace period banner */}
      {paymentStatus?.status === "grace" && paymentStatus?.grace_active && (
        <GraceBanner graceUntil={paymentStatus.grace_until} plan={paymentStatus.plan} />
      )}

      {/* Pending review banner */}
      {paymentStatus?.status === "review" && (
        <div className="bg-brand-50 border border-brand-200 rounded-xl p-4 flex items-start gap-3">
          <Clock size={17} weight="duotone" className="text-brand-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-brand-800">Tu comprobante está en revisión</p>
            <p className="text-xs text-brand-600 mt-0.5">
              Lo revisaremos en las próximas horas. Si pagaste el monto correcto, se activará tu plan.
            </p>
          </div>
        </div>
      )}

      {/* Trust card for verified payers */}
      {trustInfo && trustInfo.verified_payments_count >= 1 && (
        <TrustCard trustInfo={trustInfo} />
      )}

      {/* Feature gate highlight from URL */}
      {searchParams.get("feature") && (
        <div className="bg-brand-50 border border-brand-200 rounded-xl p-4 flex items-center gap-3">
          <Lock size={16} weight="duotone" className="text-brand-500" />
          <p className="text-sm text-brand-700">
            <strong>
              {searchParams.get("feature").replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
            </strong>{" "}
            está disponible en los planes de pago. Elige uno para desbloquear.
          </p>
        </div>
      )}

      {/* Plans grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6">
        {PLANS.map((plan) => {
          const isDowngrade =
            PLANS.findIndex((p) => p.key === userPlan) > PLANS.findIndex((p) => p.key === plan.key);

          return (
            <PlanCard
              key={plan.key}
              plan={plan}
              currentPlan={userPlan}
              onSelect={openPaymentModal}
              isDowngrade={isDowngrade}
            />
          );
        })}
      </div>

      {/* Trust badges */}
      <div className="flex flex-wrap items-center justify-center gap-6">
        <div className="flex items-center gap-2 text-xs text-ink-400">
          <ShieldCheck size={15} weight="duotone" className="text-accent-600" />
          <span>Pago seguro por transferencia Bre-B</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-ink-400">
          <Lightning size={15} weight="duotone" className="text-brand-500" />
          <span>Activación en máx. 24h</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-ink-400">
          <X size={13} className="text-ink-300" />
          <span>Cancela cuando quieras</span>
        </div>
      </div>

      {/* Comparison table for larger screens */}
      <div className="hidden lg:block mt-12">
        <h2 className="text-lg font-bold text-ink-900 text-center mb-6">Comparación detallada</h2>
        <ComparisonTable plans={PLANS} currentPlan={userPlan} />
      </div>

      {/* Payment Modal */}
      {selectedPlan && (
        <PaymentModal
          plan={selectedPlan}
          checkout={checkout}
          loading={loadingCheckout}
          onClose={closePaymentModal}
          onSuccess={handlePaymentSuccess}
        />
      )}
    </div>
  );
}

// =============================================================================
// COMPARISON TABLE
// =============================================================================
function ComparisonTable({ plans, currentPlan }) {
  const features = [
    { key: "searches", label: "Búsquedas/día", values: ["10", "∞", "∞", "∞", "∞"] },
    { key: "favorites", label: "Favoritos", values: ["10", "100", "∞", "∞", "∞"] },
    { key: "alerts", label: "Alertas/semana", values: ["—", "50", "∞", "∞", "∞"] },
    { key: "description", label: "Descripción completa", values: [false, true, true, true, true] },
    { key: "score", label: "Match score", values: [false, true, true, true, true] },
    { key: "amount", label: "Ver montos", values: [false, true, true, true, true] },
    { key: "export", label: "Exportar/mes", values: ["—", "50", "500", "∞", "∞"] },
    { key: "private", label: "Contratos privados", values: [false, false, true, true, true] },
    { key: "ai", label: "Análisis IA", values: [false, false, true, true, true] },
    { key: "pipeline", label: "Pipeline CRM", values: [false, false, true, true, true] },
    { key: "push", label: "Alertas push", values: [false, false, true, true, true] },
    { key: "history", label: "Historial", values: ["7 días", "30 días", "1 año", "2 años", "Todo"] },
    { key: "team", label: "Multi-usuario", values: ["1", "1", "1", "2", "5"] },
    { key: "reports", label: "Reportes automáticos", values: [false, false, false, true, true] },
    { key: "intel", label: "Inteligencia competitiva", values: [false, false, false, false, true] },
    { key: "api", label: "API access", values: [false, false, false, false, true] },
    { key: "support", label: "Soporte", values: ["—", "Email 48h", "Email 24h", "Email 12h", "WhatsApp 4h"] },
  ];

  return (
    <div className="overflow-x-auto rounded-2xl border border-surface-border">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="text-left p-3 border-b border-surface-border bg-surface-bg" />
            {plans.map((plan) => (
              <th
                key={plan.key}
                className={`text-center p-3 border-b border-surface-border ${
                  plan.popular ? "bg-brand-50" : "bg-surface-bg"
                }`}
              >
                <div className="flex flex-col items-center gap-1">
                  <span className="text-xl">{plan.emoji}</span>
                  <span className="font-bold text-sm text-ink-900">{plan.displayName}</span>
                  <span className="text-xs text-ink-400">
                    {plan.price === 0 ? "Gratis" : money(plan.price)}
                  </span>
                  {currentPlan === plan.key && (
                    <Badge color="green" className="mt-1">Actual</Badge>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {features.map((f) => (
            <tr key={f.key} className="hover:bg-surface-hover">
              <td className="p-3 border-b border-surface-border text-xs font-medium text-ink-600">
                {f.label}
              </td>
              {f.values.map((v, i) => (
                <td
                  key={i}
                  className={`text-center p-3 border-b border-surface-border ${
                    plans[i].popular ? "bg-brand-50/30" : ""
                  }`}
                >
                  {typeof v === "boolean" ? (
                    v ? (
                      <Check size={16} weight="bold" className="text-accent-600 mx-auto" />
                    ) : (
                      <X size={15} className="text-ink-200 mx-auto" />
                    )
                  ) : (
                    <span className="text-xs text-ink-600">{v}</span>
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
