import { useState, useEffect } from "react";
import Modal from "../ui/Modal";
import Button from "../ui/Button";
import Spinner from "../ui/Spinner";
import PaymentMethodBox from "./PaymentMethodBox";
import { money } from "../../lib/format";
import { api } from "../../lib/api";
import { useToast } from "../ui/Toast";
import {
  Zap,
  Copy,
  ChevronRight,
  Upload,
  ImageIcon,
} from "lucide-react";

/**
 * Payment modal with checkout flow
 */
export default function PaymentModal({
  plan,
  checkout,
  loading,
  onClose,
  onSuccess,
}) {
  const toast = useToast();
  const [comprobante, setComprobante] = useState(null);
  const [comprobantePreview, setComprobantePreview] = useState(null);
  const [confirming, setConfirming] = useState(false);

  // Revoke object URL on unmount or when preview changes to prevent memory leak
  useEffect(() => {
    return () => {
      if (comprobantePreview) URL.revokeObjectURL(comprobantePreview);
    };
  }, [comprobantePreview]);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copiado");
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

    if (comprobantePreview) URL.revokeObjectURL(comprobantePreview);
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

      if (result.status === "approved") {
        toast.success(`¡Plan ${result.plan} activado! Disfruta Jobper.`);

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

        onSuccess(result);
      } else if (result.status === "grace") {
        toast.info(`Acceso temporal activado por ${result.grace_hours || 12}h mientras verificamos tu pago.`);
        onSuccess(result);
      } else if (result.status === "review") {
        toast.info("¡Recibido! Tu pago está en revisión. Te avisamos en máximo 24 horas.");
        onClose();
      } else if (result.status === "rejected") {
        const issues = result.issues?.join(", ") || result.message || "Comprobante no válido";
        toast.error(`Verificación fallida: ${issues}. Puedes intentar de nuevo.`);
        setComprobante(null);
        setComprobantePreview(null);
      }
    } catch (err) {
      if (err.status === "review") {
        toast.info(err.message || "Tu comprobante está siendo revisado manualmente.");
        onClose();
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

  const breb = checkout?.payment_methods?.breb;
  const nequi = checkout?.payment_methods?.nequi;
  const banco = checkout?.payment_methods?.bancolombia;

  return (
    <Modal open={true} onClose={onClose}>
      <div className="space-y-5">
        <div className="text-center">
          <div
            className={`inline-flex items-center justify-center w-14 h-14 rounded-full mb-3 ${
              plan.color === "blue" ? "bg-blue-100" : ""
            } ${plan.color === "purple" ? "bg-purple-100" : ""} ${
              plan.color === "amber" ? "bg-amber-100" : ""
            }`}
          >
            <span className="text-3xl">{plan.emoji}</span>
          </div>
          <h2 className="text-xl font-bold text-gray-900">Activar {plan.displayName}</h2>
          <p className="text-2xl font-bold text-brand-600 mt-1">
            {checkout?.amount_display || money(plan.price) + " COP"}
            <span className="text-sm font-normal text-gray-500">/mes</span>
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-6">
            <Spinner />
          </div>
        ) : checkout ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-600 text-center">{checkout.instructions}</p>

            <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2.5 flex items-center gap-2 text-sm text-blue-800">
              <Zap className="h-4 w-4 text-blue-500 flex-shrink-0" />
              <span>
                Tu plan se activa en <strong>máximo 24 horas</strong> una vez verifiquemos tu pago.
              </span>
            </div>

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
                  Copia este código y pégalo en la <strong>descripción/concepto</strong> de tu
                  transferencia.
                  <br />
                  Sin el código, no podremos verificar tu pago automáticamente.
                </p>
              </div>
            )}

            {/* Payment Methods */}
            {breb?.handle && (
              <PaymentMethodBox
                color="green"
                title="Bre-B — Cualquier banco"
                value={breb.handle}
                footer="Funciona con Nequi, Daviplata, Bancolombia, Bancoomeva y más"
                recommended
                onCopy={copyToClipboard}
              />
            )}

            {nequi?.number && (
              <PaymentMethodBox
                color="purple"
                title={nequi.name}
                value={nequi.number}
                onCopy={copyToClipboard}
              />
            )}

            {banco?.account && (
              <PaymentMethodBox
                color="yellow"
                title={banco.name}
                subtitle={banco.type}
                value={banco.account}
                footer={banco.holder}
                onCopy={copyToClipboard}
              />
            )}

            {/* Comprobante upload */}
            <div className="border-t border-gray-200 pt-4 space-y-3">
              <p className="text-sm font-medium text-gray-700">¿Ya transferiste? Sube tu comprobante:</p>

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
                    <span className="text-sm text-gray-500">Seleccionar imagen del comprobante</span>
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
                Verificamos tu comprobante con IA. Si todo está correcto, tu plan se activa al
                instante.
              </p>
            </div>
          </div>
        ) : null}
      </div>
    </Modal>
  );
}
