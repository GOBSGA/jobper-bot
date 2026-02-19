import Card from "../ui/Card";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import { money } from "../../lib/format";
import {
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  AlertTriangle,
} from "lucide-react";

// Helper functions
const formatDate = (dateStr) => {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleString("es-CO", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getStatusBadge = (status) => {
  switch (status) {
    case "grace":
      return (
        <Badge color="green">
          <CheckCircle className="h-3 w-3 mr-1" />
          Gracia 24h
        </Badge>
      );
    case "review":
      return (
        <Badge color="yellow">
          <Clock className="h-3 w-3 mr-1" />
          Revisión manual
        </Badge>
      );
    case "pending":
      return (
        <Badge color="gray">
          <Clock className="h-3 w-3 mr-1" />
          Pendiente
        </Badge>
      );
    case "approved":
      return (
        <Badge color="green">
          <CheckCircle className="h-3 w-3 mr-1" />
          Aprobado
        </Badge>
      );
    case "rejected":
      return (
        <Badge color="red">
          <XCircle className="h-3 w-3 mr-1" />
          Rechazado
        </Badge>
      );
    default:
      return <Badge color="gray">{status}</Badge>;
  }
};

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.7) return "text-green-600";
  if (confidence >= 0.4) return "text-yellow-600";
  return "text-red-600";
};

/**
 * Individual payment card for admin review
 */
export default function PaymentCard({ payment, onApprove, onReject, disabled }) {
  return (
    <Card className="p-4">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-lg font-bold text-gray-900">{money(payment.amount)}</span>
            {getStatusBadge(payment.status)}
            {payment.status === "grace" && (
              <span className="bg-green-100 text-green-800 text-xs font-bold px-2 py-0.5 rounded-full">
                ⚡ Acceso temporal activo
              </span>
            )}
            {payment.grace_until && (
              <span className="text-xs text-amber-700">
                Expira: {formatDate(payment.grace_until)}
              </span>
            )}
          </div>

          <div className="text-sm text-gray-600 space-y-1">
            <p>
              <strong>Usuario:</strong> {payment.user_email} (ID: {payment.user_id})
            </p>
            <p>
              <strong>Plan:</strong> {payment.plan || "—"}
            </p>
            <p>
              <strong>Referencia:</strong>{" "}
              <code className="bg-gray-100 px-1 rounded">{payment.reference || "—"}</code>
            </p>
            <p>
              <strong>Fecha:</strong> {formatDate(payment.created_at)}
            </p>
          </div>

          {payment.verification && (
            <div className="mt-3 p-3 bg-gray-50 rounded-lg space-y-2">
              <p className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <Eye className="h-4 w-4" />
                Verificación IA
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">Confianza:</span>
                  <span
                    className={`ml-1 font-bold ${getConfidenceColor(
                      payment.verification.confidence
                    )}`}
                  >
                    {Math.round((payment.verification.confidence || 0) * 100)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Monto detectado:</span>
                  <span className="ml-1 font-medium">
                    {payment.verification.extracted_amount
                      ? money(payment.verification.extracted_amount)
                      : "—"}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Referencia detectada:</span>
                  <span className="ml-1 font-medium">
                    {payment.verification.extracted_reference || "—"}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Fecha detectada:</span>
                  <span className="ml-1 font-medium">
                    {payment.verification.extracted_date || "—"}
                  </span>
                </div>
              </div>

              {payment.verification.issues?.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-amber-700 flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    Problemas detectados:
                  </p>
                  <ul className="text-xs text-amber-600 list-disc list-inside mt-1">
                    {payment.verification.issues.map((issue, i) => (
                      <li key={i}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {payment.comprobante_url && (
            <div className="mt-3">
              <a
                href={payment.comprobante_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-brand-600 hover:underline flex items-center gap-1"
              >
                <Eye className="h-4 w-4" />
                Ver comprobante
              </a>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <Button variant="primary" onClick={() => onApprove(payment)} disabled={disabled}>
            <CheckCircle className="h-4 w-4 mr-1" />
            Aprobar
          </Button>
          <Button variant="secondary" onClick={() => onReject(payment)} disabled={disabled}>
            <XCircle className="h-4 w-4 mr-1" />
            Rechazar
          </Button>
        </div>
      </div>
    </Card>
  );
}
