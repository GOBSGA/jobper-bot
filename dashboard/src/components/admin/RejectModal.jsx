import { useState } from "react";
import Modal from "../ui/Modal";
import Button from "../ui/Button";
import Spinner from "../ui/Spinner";
import { money } from "../../lib/format";
import { XCircle } from "lucide-react";

/**
 * Modal for rejecting payments with reason
 */
export default function RejectModal({ payment, onConfirm, onCancel, loading }) {
  const [reason, setReason] = useState("");

  const handleConfirm = () => {
    if (!reason.trim()) return;
    onConfirm(reason);
  };

  return (
    <Modal onClose={onCancel}>
      <div className="p-6 space-y-4">
        <h3 className="text-lg font-bold text-gray-900">Rechazar Pago</h3>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">
            Rechazando pago de <strong>{money(payment.amount)}</strong> de{" "}
            <strong>{payment.user_email}</strong>
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Motivo del rechazo (será enviado al usuario):
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
            rows={4}
            placeholder="Ej: El monto no coincide, la referencia es incorrecta, no se ve claramente el comprobante..."
            disabled={loading}
          />
        </div>

        <div className="flex gap-2 pt-2">
          <Button
            variant="secondary"
            onClick={handleConfirm}
            disabled={!reason.trim() || loading}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white"
          >
            {loading ? (
              <>
                <Spinner className="h-4 w-4 mr-2" />
                Rechazando...
              </>
            ) : (
              <>
                <XCircle className="h-4 w-4 mr-2" />
                Confirmar rechazo
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
