import { useState } from "react";
import Modal from "../ui/Modal";
import Button from "../ui/Button";
import Spinner from "../ui/Spinner";
import { money } from "../../lib/format";
import { CheckCircle, CheckSquare, Square, Image, ExternalLink } from "lucide-react";

const PLAN_LABELS = {
  free: "Free",
  alertas: "Alertas ($49,900)",
  competidor: "Competidor ($149,900)",
  cazador: "Cazador ($299,900)",
  business: "Business ($499,900)",
  dominador: "Dominador ($599,900)",
};

/**
 * Modal for approving payments with verification checklist and inline receipt
 */
export default function ApprovalModal({ payment, onConfirm, onCancel, loading }) {
  const [checklist, setChecklist] = useState({
    moneyReceived: false,
    amountCorrect: false,
    referenceMatch: false,
  });

  const BASE = import.meta.env.VITE_API_URL || "/api";
  const comprobanteUrl = `${BASE}/admin/payments/${payment.id}/comprobante`;
  const hasComprobante = Boolean(payment.comprobante_url);
  const planLabel = PLAN_LABELS[payment.plan] || payment.plan || "—";

  const toggleChecklist = (key) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const allChecked = checklist.moneyReceived && checklist.amountCorrect && checklist.referenceMatch;

  return (
    <Modal onClose={onCancel}>
      <div className="p-6 space-y-4 max-w-lg">
        <h3 className="text-lg font-bold text-gray-900">Confirmar Activación de Plan</h3>

        {/* Payment summary */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-1">
          <p className="text-sm text-blue-800">
            Activando <strong>{planLabel}</strong> para{" "}
            <strong>{payment.user_email}</strong>
          </p>
          <p className="text-sm text-blue-700">
            Monto: <strong>{money(payment.amount)}</strong>
          </p>
          <p className="text-xs text-blue-600">
            Referencia: <code className="bg-blue-100 px-1 rounded">{payment.reference}</code>
          </p>
        </div>

        {/* Inline receipt */}
        {hasComprobante ? (
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700 flex items-center gap-1">
              <Image className="h-4 w-4" />
              Comprobante subido por el usuario:
            </p>
            <div className="relative rounded-lg overflow-hidden border border-gray-200 bg-gray-50">
              <img
                src={comprobanteUrl}
                alt="Comprobante"
                className="w-full max-h-64 object-contain"
                onError={(e) => {
                  e.target.style.display = "none";
                  e.target.nextSibling.style.display = "flex";
                }}
              />
              <div
                className="hidden items-center justify-center h-20 text-xs text-gray-400"
                style={{ display: "none" }}
              >
                No se pudo cargar imagen
              </div>
              <a
                href={comprobanteUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="absolute top-2 right-2 bg-white rounded-lg p-1 shadow text-gray-600 hover:text-gray-900"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>
        ) : (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-700 flex items-center gap-2">
            <Image className="h-4 w-4 flex-shrink-0" />
            Este pago no tiene pantallazo. Verifica manualmente en tu Bre-B antes de aprobar.
          </div>
        )}

        {/* Checklist */}
        <div className="space-y-3">
          <p className="text-sm font-medium text-gray-700">Confirma que verificaste:</p>

          {[
            { key: "moneyReceived", label: `El dinero de ${money(payment.amount)} llegó a tu cuenta Bre-B/Nequi` },
            { key: "amountCorrect", label: `El monto recibido es exactamente ${money(payment.amount)}` },
            { key: "referenceMatch", label: `La referencia coincide: ${payment.reference || "—"}` },
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
            ⚠️ Debes confirmar todos los puntos antes de activar el plan
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
              <>
                <Spinner className="h-4 w-4 mr-2" />
                Activando...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4 mr-2" />
                Activar {planLabel.split(" ")[0]}
              </>
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
