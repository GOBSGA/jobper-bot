import { useState } from "react";
import Modal from "../ui/Modal";
import Button from "../ui/Button";
import Spinner from "../ui/Spinner";
import { money } from "../../lib/format";
import { CheckCircle, CheckSquare, Square } from "lucide-react";

/**
 * Modal for approving payments with verification checklist
 */
export default function ApprovalModal({ payment, onConfirm, onCancel, loading }) {
  const [checklist, setChecklist] = useState({
    moneyReceived: false,
    amountCorrect: false,
    referenceMatch: false,
  });

  const toggleChecklist = (key) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const allChecked = checklist.moneyReceived && checklist.amountCorrect && checklist.referenceMatch;

  const handleConfirm = () => {
    if (!allChecked) return;
    onConfirm();
  };

  return (
    <Modal onClose={onCancel}>
      <div className="p-6 space-y-4">
        <h3 className="text-lg font-bold text-gray-900">Confirmar Aprobación</h3>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            Aprobando pago de <strong>{money(payment.amount)}</strong> para{" "}
            <strong>{payment.user_email}</strong>
          </p>
          <p className="text-xs text-blue-600 mt-1">
            Referencia: <code className="bg-blue-100 px-1 rounded">{payment.reference}</code>
          </p>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-gray-700">
            Confirma que verificaste lo siguiente:
          </p>

          <label className="flex items-start gap-3 cursor-pointer group">
            <button
              type="button"
              onClick={() => toggleChecklist("moneyReceived")}
              className="flex-shrink-0 mt-0.5"
            >
              {checklist.moneyReceived ? (
                <CheckSquare className="h-5 w-5 text-green-600" />
              ) : (
                <Square className="h-5 w-5 text-gray-400 group-hover:text-gray-600" />
              )}
            </button>
            <span className="text-sm text-gray-700">
              ✅ El dinero <strong>realmente llegó</strong> a tu cuenta Bre-B/Nequi
            </span>
          </label>

          <label className="flex items-start gap-3 cursor-pointer group">
            <button
              type="button"
              onClick={() => toggleChecklist("amountCorrect")}
              className="flex-shrink-0 mt-0.5"
            >
              {checklist.amountCorrect ? (
                <CheckSquare className="h-5 w-5 text-green-600" />
              ) : (
                <Square className="h-5 w-5 text-gray-400 group-hover:text-gray-600" />
              )}
            </button>
            <span className="text-sm text-gray-700">
              💵 El monto recibido es <strong>exactamente {money(payment.amount)}</strong>
            </span>
          </label>

          <label className="flex items-start gap-3 cursor-pointer group">
            <button
              type="button"
              onClick={() => toggleChecklist("referenceMatch")}
              className="flex-shrink-0 mt-0.5"
            >
              {checklist.referenceMatch ? (
                <CheckSquare className="h-5 w-5 text-green-600" />
              ) : (
                <Square className="h-5 w-5 text-gray-400 group-hover:text-gray-600" />
              )}
            </button>
            <span className="text-sm text-gray-700">
              🔖 La referencia coincide:{" "}
              <code className="bg-gray-100 px-1 rounded text-xs">{payment.reference}</code>
            </span>
          </label>
        </div>

        {!allChecked && (
          <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-2">
            ⚠️ Debes confirmar todos los puntos antes de aprobar
          </p>
        )}

        <div className="flex gap-2 pt-2">
          <Button
            variant="primary"
            onClick={handleConfirm}
            disabled={!allChecked || loading}
            className="flex-1"
          >
            {loading ? (
              <>
                <Spinner className="h-4 w-4 mr-2" />
                Aprobando...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4 mr-2" />
                Aprobar pago
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
