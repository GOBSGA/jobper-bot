import { useState, useEffect } from "react";
import Modal from "../ui/Modal";
import Button from "../ui/Button";
import Spinner from "../ui/Spinner";
import PaymentMethodBox from "./PaymentMethodBox";
import { money } from "../../lib/format";
import { api } from "../../lib/api";
import { useToast } from "../ui/Toast";
import {
  Lightning,
  Copy,
  ArrowRight,
  UploadSimple,
  Image,
  Warning,
} from "@phosphor-icons/react";

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
        if (result.rewards?.length > 0) {
          result.rewards.forEach((reward) => {
            setTimeout(() => toast.success(reward.message), 1500);
          });
        } else if (result.trust?.points_earned) {
          setTimeout(() => toast.info(`+${result.trust.points_earned} puntos de confianza`), 1500);
        }
        onSuccess(result);
      } else if (result.status === "grace") {
        toast.info(`Acceso temporal activado por ${result.grace_hours || 24}h mientras verificamos tu pago.`);
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
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-surface-hover mb-3">
            <span className="text-3xl">{plan.emoji}</span>
          </div>
          <h2 className="text-lg font-bold text-ink-900 tracking-snug">Activar {plan.displayName}</h2>
          <p className="text-2xl font-bold text-brand-600 mt-1 tracking-tighter">
            {checkout?.amount_display || money(plan.price) + " COP"}
            <span className="text-sm font-normal text-ink-400">/mes</span>
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-6">
            <Spinner />
          </div>
        ) : checkout ? (
          <div className="space-y-4">
            {/* Activation time notice */}
            <div className="bg-brand-50 border border-brand-200 rounded-xl px-4 py-2.5 flex items-center gap-2">
              <Lightning size={15} weight="duotone" className="text-brand-500 flex-shrink-0" />
              <span className="text-xs text-brand-700">
                Tu plan se activa en <strong>máximo 24 horas</strong> una vez verifiquemos tu pago.
              </span>
            </div>

            {/* Reference code — critical anti-fraud element */}
            {checkout.reference && (
              <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-4 text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Warning size={15} weight="duotone" className="text-amber-500" />
                  <p className="text-xs font-bold text-amber-800 uppercase tracking-wide">
                    Incluye este código en la descripción
                  </p>
                </div>
                <div className="bg-white border border-amber-200 rounded-xl p-3 mb-2">
                  <div className="flex items-center justify-center gap-2">
                    <p className="text-lg font-mono font-bold text-ink-900 tracking-widest">
                      {checkout.reference}
                    </p>
                    <button
                      onClick={() => copyToClipboard(checkout.reference)}
                      className="p-1.5 hover:bg-amber-100 rounded-lg transition"
                      title="Copiar referencia"
                    >
                      <Copy size={15} className="text-amber-600" />
                    </button>
                  </div>
                </div>
                <p className="text-2xs text-amber-700 leading-relaxed">
                  Pega este código en la <strong>descripción/concepto</strong> de tu transferencia.
                  Sin el código no podemos confirmar tu pago.
                </p>
              </div>
            )}

            {/* Payment methods */}
            {breb?.handle && (
              <PaymentMethodBox
                color="brand"
                title="Bre-B — Cualquier banco"
                value={breb.handle}
                footer="Funciona con Nequi, Daviplata, Bancolombia y más"
                recommended
                onCopy={copyToClipboard}
              />
            )}
            {nequi?.number && (
              <PaymentMethodBox
                color="accent"
                title={nequi.name || "Nequi"}
                value={nequi.number}
                onCopy={copyToClipboard}
              />
            )}
            {banco?.account && (
              <PaymentMethodBox
                color="amber"
                title={banco.name || "Bancolombia"}
                subtitle={banco.type}
                value={banco.account}
                footer={banco.holder}
                onCopy={copyToClipboard}
              />
            )}

            {/* Comprobante upload */}
            <div className="border-t border-surface-border pt-4 space-y-3">
              <p className="text-sm font-semibold text-ink-900">¿Ya transferiste? Sube tu comprobante:</p>

              <label className="flex items-center justify-center gap-2 w-full px-4 py-3 border-2 border-dashed border-surface-border rounded-2xl cursor-pointer hover:border-brand-300 hover:bg-brand-50/50 transition-colors">
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
                      className="h-12 w-12 object-cover rounded-xl"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-ink-900 truncate">{comprobante?.name}</p>
                      <p className="text-2xs text-ink-400">
                        {(comprobante?.size / 1024).toFixed(0)} KB · Toca para cambiar
                      </p>
                    </div>
                    <Image size={16} className="text-accent-600 flex-shrink-0" />
                  </div>
                ) : (
                  <>
                    <UploadSimple size={18} className="text-ink-400" />
                    <span className="text-sm text-ink-400">Seleccionar imagen del comprobante</span>
                  </>
                )}
              </label>

              <Button
                className="w-full justify-center"
                onClick={confirmPayment}
                disabled={!comprobante || confirming}
              >
                {confirming ? (
                  <>
                    <Spinner className="h-4 w-4" />
                    Verificando...
                  </>
                ) : (
                  <>
                    Verificar y activar plan
                    <ArrowRight size={14} />
                  </>
                )}
              </Button>
              <p className="text-2xs text-center text-ink-400">
                Verificamos tu comprobante con IA. Si todo está correcto, tu plan se activa al instante.
              </p>
            </div>
          </div>
        ) : null}
      </div>
    </Modal>
  );
}
