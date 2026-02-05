import { useState } from "react";
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
import { Check, Zap, Copy, Shield, Banknote, ChevronRight, Upload, ImageIcon } from "lucide-react";

const PLANS = [
  {
    key: "free",
    name: "Free",
    price: 0,
    features: [
      "Búsqueda de contratos",
      "3 alertas por semana",
      "5 favoritos máximo",
    ],
  },
  {
    key: "alertas",
    name: "Alertas",
    price: 29900,
    features: [
      "Todo de Free",
      "Alertas ilimitadas",
      "Favoritos ilimitados",
      "Match score por contrato",
      "Email digest diario",
    ],
  },
  {
    key: "business",
    name: "Business",
    price: 149900,
    popular: true,
    features: [
      "Todo de Alertas",
      "Pipeline de ventas",
      "Push notifications instantáneas",
      "Marketplace",
      "Análisis IA de contratos",
      "Reportes y documentos",
    ],
  },
  {
    key: "enterprise",
    name: "Enterprise",
    price: 599900,
    features: [
      "Todo de Business",
      "Equipo multiusuario",
      "API access",
      "Inteligencia competitiva",
      "Soporte prioritario",
    ],
  },
];

export default function Plans() {
  const { user, refresh } = useAuth();
  const { data: sub, loading } = useApi("/payments/subscription");
  const toast = useToast();
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [showPayment, setShowPayment] = useState(false);
  const [checkout, setCheckout] = useState(null);
  const [loadingCheckout, setLoadingCheckout] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [comprobante, setComprobante] = useState(null);
  const [comprobantePreview, setComprobantePreview] = useState(null);

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
      toast.success(`¡Plan ${result.plan} activado! Disfruta Jobper.`);
      await refresh();
      setShowPayment(false);
      setSelectedPlan(null);
      setCheckout(null);
      setComprobante(null);
      setComprobantePreview(null);
    } catch (err) {
      toast.error(err.error || "Error confirmando pago");
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

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;

  const nequi = checkout?.payment_methods?.nequi;
  const banco = checkout?.payment_methods?.bancolombia;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Tu plan</h1>

      {sub?.subscription && (
        <Card className="bg-brand-50 border-brand-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-brand-800">Plan {sub.subscription.plan}</p>
              <p className="text-sm text-brand-600">Activo hasta {date(sub.subscription.ends_at)}</p>
              {sub.subscription.days_remaining <= 5 && (
                <p className="text-sm text-red-600 font-medium mt-1">
                  Vence en {sub.subscription.days_remaining} días
                </p>
              )}
            </div>
            <Button variant="secondary" size="sm" onClick={cancel}>Cancelar</Button>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {PLANS.map((plan) => {
          const isCurrent = user?.plan === plan.key || (plan.key === "free" && (!user?.plan || user?.plan === "trial" || user?.plan === "expired"));
          return (
            <Card key={plan.key} className={plan.popular ? "ring-2 ring-brand-600 relative" : ""}>
              {plan.popular && (
                <Badge color="blue" className="absolute -top-2.5 left-4">
                  <Zap className="h-3 w-3 mr-1" /> Popular
                </Badge>
              )}
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {plan.price === 0 ? "Gratis" : <>{money(plan.price)}<span className="text-sm font-normal text-gray-500">/mes</span></>}
                  </p>
                </div>
                <ul className="space-y-2">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                      <Check className="h-4 w-4 text-green-500 flex-shrink-0" /> {f}
                    </li>
                  ))}
                </ul>
                <Button
                  className="w-full"
                  variant={plan.popular ? "primary" : "secondary"}
                  onClick={() => openPaymentModal(plan)}
                  disabled={isCurrent || plan.price === 0}
                >
                  {isCurrent ? "Plan actual" : plan.price === 0 ? "Plan gratuito" : "Elegir plan"}
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      <div className="flex items-center justify-center gap-2 text-xs text-gray-400">
        <Shield className="h-3.5 w-3.5" />
        <span>Pago por transferencia. Cancela cuando quieras. Sin compromiso.</span>
      </div>

      {/* Payment Modal */}
      {showPayment && selectedPlan && (
        <Modal open={true} onClose={() => { setShowPayment(false); setSelectedPlan(null); setCheckout(null); setComprobante(null); setComprobantePreview(null); }}>
          <div className="space-y-5">
            <div className="text-center">
              <Banknote className="h-10 w-10 text-brand-600 mx-auto mb-2" />
              <h2 className="text-xl font-bold text-gray-900">Activar plan {selectedPlan.name}</h2>
              <p className="text-2xl font-bold text-brand-600 mt-1">
                {checkout?.amount_display || money(selectedPlan.price) + " COP"}
                <span className="text-sm font-normal text-gray-500">/mes</span>
              </p>
            </div>

            {loadingCheckout ? (
              <div className="flex justify-center py-6"><Spinner /></div>
            ) : checkout ? (
              <div className="space-y-4">
                <p className="text-sm text-gray-600 text-center">{checkout.instructions}</p>

                {checkout.reference && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500">Referencia de pago</p>
                    <div className="flex items-center justify-center gap-2 mt-1">
                      <p className="text-sm font-mono font-semibold text-gray-900">{checkout.reference}</p>
                      <button onClick={() => copyToClipboard(checkout.reference)} className="p-1 hover:bg-gray-200 rounded">
                        <Copy className="h-3.5 w-3.5 text-gray-500" />
                      </button>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">Incluye esta referencia en la descripción del pago</p>
                  </div>
                )}

                {/* Nequi */}
                {nequi?.number && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-purple-600 font-semibold uppercase tracking-wide">{nequi.name}</p>
                        <p className="text-lg text-purple-800 font-mono font-bold mt-1">{nequi.number}</p>
                      </div>
                      <button onClick={() => copyToClipboard(nequi.number)} className="p-2 hover:bg-purple-100 rounded-lg transition">
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
                        <p className="text-lg text-yellow-800 font-mono font-bold">{banco.account}</p>
                        <p className="text-xs text-yellow-700 mt-0.5">{banco.holder}</p>
                      </div>
                      <button onClick={() => copyToClipboard(banco.account)} className="p-2 hover:bg-yellow-100 rounded-lg transition">
                        <Copy className="h-4 w-4 text-yellow-600" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Comprobante upload */}
                <div className="border-t border-gray-200 pt-4 space-y-3">
                  <p className="text-sm font-medium text-gray-700">¿Ya transferiste? Sube tu comprobante:</p>

                  <label className="flex items-center justify-center gap-2 w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer hover:border-brand-400 hover:bg-brand-50/50 transition">
                    <input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={handleComprobanteChange} />
                    {comprobantePreview ? (
                      <div className="flex items-center gap-3 w-full">
                        <img src={comprobantePreview} alt="Comprobante" className="h-12 w-12 object-cover rounded-lg" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-800 truncate">{comprobante?.name}</p>
                          <p className="text-xs text-gray-500">{(comprobante?.size / 1024).toFixed(0)} KB — Toca para cambiar</p>
                        </div>
                        <ImageIcon className="h-4 w-4 text-green-500" />
                      </div>
                    ) : (
                      <>
                        <Upload className="h-5 w-5 text-gray-400" />
                        <span className="text-sm text-gray-500">Seleccionar imagen del comprobante</span>
                      </>
                    )}
                  </label>

                  <Button className="w-full h-12 text-base" onClick={confirmPayment} disabled={!comprobante || confirming}>
                    {confirming ? <Spinner className="h-5 w-5" /> : (
                      <>Confirmar pago y activar plan <ChevronRight className="h-4 w-4" /></>
                    )}
                  </Button>
                  <p className="text-xs text-center text-gray-400">
                    Tu plan se activa inmediatamente al subir el comprobante.
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
