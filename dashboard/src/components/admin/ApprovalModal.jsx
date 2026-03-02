import { useState, useEffect } from "react";
import Modal from "../ui/Modal";
import Button from "../ui/Button";
import Spinner from "../ui/Spinner";
import { money } from "../../lib/format";
import { getAccessToken } from "../../lib/storage";
import { PLAN_LABELS } from "./PaymentCard";
import { CheckCircle, CheckSquare, Square, Image, ExternalLink } from "lucide-react";

function AuthImage({ paymentId, className }) {
  const [src, setSrc] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let objectUrl = null;
    const BASE = import.meta.env.VITE_API_URL || "/api";
    fetch(`${BASE}/admin/payments/${paymentId}/comprobante`, {
      headers: { Authorization: `Bearer ${getAccessToken()}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("no image");
        return res.blob();
      })
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));

    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [paymentId]);

  if (loading) return (
    <div className="flex items-center justify-center h-32 bg-gray-50 rounded-lg">
      <Spinner className="h-5 w-5" />
    </div>
  );
  if (error || !src) return (
    <div className="flex items-center justify-center h-20 bg-gray-50 rounded-lg text-xs text-gray-400">
      No se pudo cargar la imagen
    </div>
  );
  return <img src={src} alt="Comprobante" className={className} />;
}

export default function ApprovalModal({ payment, onConfirm, onCancel, loading }) {
  const [checklist, setChecklist] = useState({
    moneyReceived: false,
    amountCorrect: false,
    referenceMatch: false,
  });

  const hasComprobante = Boolean(payment.comprobante_url);
  const planLabel = PLAN_LABELS[payment.plan] || payment.plan || "—";
  const planName = planLabel.split(" —")[0];

  const toggleChecklist = (key) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const allChecked = checklist.moneyReceived && checklist.amountCorrect && checklist.referenceMatch;

  return (
    <Modal onClose={onCancel}>
      <div className="p-6 space-y-4 w-full max-w-md">
        <h3 className="text-lg font-bold text-gray-900">Activar {planName}</h3>

        {/* Summary */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 space-y-0.5 text-sm">
          <p className="text-blue-800">
            Plan: <strong>{planLabel}</strong>
          </p>
          <p className="text-blue-800">
            Usuario: <strong>{payment.user_email}</strong>
          </p>
          <p className="text-blue-700">
            Monto: <strong>{money(payment.amount)}</strong> ·{" "}
            Ref: <code className="bg-blue-100 px-1 rounded text-xs">{payment.reference}</code>
          </p>
        </div>

        {/* Receipt image */}
        {hasComprobante ? (
          <div className="space-y-1.5">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide flex items-center gap-1">
              <Image className="h-3.5 w-3.5" /> Pantallazo del cliente
            </p>
            <div className="rounded-xl overflow-hidden border border-gray-200">
              <AuthImage
                paymentId={payment.id}
                className="w-full max-h-72 object-contain bg-gray-50"
              />
            </div>
          </div>
        ) : (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-700 flex items-center gap-2">
            <Image className="h-4 w-4 flex-shrink-0" />
            Sin pantallazo — verifica en tu Bre-B antes de aprobar.
          </div>
        )}

        {/* Checklist */}
        <div className="space-y-2.5">
          <p className="text-sm font-medium text-gray-700">Confirma antes de activar:</p>
          {[
            { key: "moneyReceived", label: `El dinero (${money(payment.amount)}) ya llegó a tu cuenta` },
            { key: "amountCorrect", label: `El monto es correcto` },
            { key: "referenceMatch", label: `La referencia "${payment.reference || "—"}" coincide` },
          ].map(({ key, label }) => (
            <label key={key} className="flex items-start gap-3 cursor-pointer group">
              <button type="button" onClick={() => toggleChecklist(key)} className="flex-shrink-0 mt-0.5">
                {checklist[key] ? (
                  <CheckSquare className="h-5 w-5 text-green-600" />
                ) : (
                  <Square className="h-5 w-5 text-gray-400 group-hover:text-gray-600" />
                )}
              </button>
              <span className="text-sm text-gray-700">{label}</span>
            </label>
          ))}
        </div>

        {!allChecked && (
          <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-2">
            ⚠️ Marca los tres puntos antes de activar
          </p>
        )}

        <div className="flex gap-2 pt-1">
          <Button
            variant="primary"
            onClick={onConfirm}
            disabled={!allChecked || loading}
            className="flex-1"
          >
            {loading ? (
              <><Spinner className="h-4 w-4 mr-2" />Activando...</>
            ) : (
              <><CheckCircle className="h-4 w-4 mr-2" />Activar {planName}</>
            )}
          </Button>
          <Button variant="secondary" onClick={onCancel} disabled={loading}>
            Cancelar
          </Button>
        </div>
      </div>
    </Modal>
  );
}
