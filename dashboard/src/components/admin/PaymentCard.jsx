import { useState } from "react";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import { money } from "../../lib/format";
import { getAccessToken } from "../../lib/storage";
import {
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  AlertTriangle,
  Image,
  ExternalLink,
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

const PLAN_LABELS = {
  free: "Free",
  alertas: "Alertas ($49,900)",
  competidor: "Competidor ($149,900)",
  cazador: "Cazador ($299,900)",
  business: "Business ($499,900)",
  dominador: "Dominador ($599,900)",
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
  const [showImage, setShowImage] = useState(false);
  const BASE = import.meta.env.VITE_API_URL || "/api";
  const comprobanteImgUrl = `${BASE}/admin/payments/${payment.id}/comprobante`;
  const hasComprobante = Boolean(payment.comprobante_url);
  const planLabel = PLAN_LABELS[payment.plan] || payment.plan || "—";

  return (
    <Card className="p-4">
      <div className="flex items-start gap-4">
        {/* Main content */}
        <div className="flex-1 space-y-3 min-w-0">
          {/* Header row */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-xl font-bold text-gray-900">{money(payment.amount)}</span>
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

          {/* Payment details */}
          <div className="text-sm text-gray-600 grid grid-cols-2 gap-x-6 gap-y-1">
            <p>
              <span className="text-gray-400">Usuario:</span>{" "}
              <strong className="text-gray-800">{payment.user_email}</strong>
            </p>
            <p>
              <span className="text-gray-400">Plan:</span>{" "}
              <strong className="text-gray-800">{planLabel}</strong>
            </p>
            <p>
              <span className="text-gray-400">Referencia:</span>{" "}
              <code className="bg-gray-100 px-1 rounded text-xs">{payment.reference || "—"}</code>
            </p>
            <p>
              <span className="text-gray-400">Fecha:</span> {formatDate(payment.created_at)}
            </p>
            <p className="col-span-2">
              <span className="text-gray-400">ID:</span>{" "}
              <span className="text-gray-500">usuario #{payment.user_id} · pago #{payment.id}</span>
            </p>
          </div>

          {/* AI verification block */}
          {payment.verification && (
            <div className="p-3 bg-gray-50 rounded-lg space-y-2">
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

          {/* Comprobante image */}
          {hasComprobante ? (
            <div className="space-y-2">
              <button
                onClick={() => setShowImage((v) => !v)}
                className="flex items-center gap-2 text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                <Image className="h-4 w-4" />
                {showImage ? "Ocultar comprobante" : "Ver comprobante (pantallazo)"}
              </button>

              {showImage && (
                <div className="relative rounded-lg overflow-hidden border border-gray-200 bg-gray-50">
                  <img
                    src={comprobanteImgUrl}
                    alt="Comprobante de pago"
                    className="w-full max-h-96 object-contain"
                    onError={(e) => {
                      e.target.style.display = "none";
                      e.target.nextSibling.style.display = "flex";
                    }}
                  />
                  <div
                    className="hidden items-center justify-center h-32 text-sm text-gray-500"
                    style={{ display: "none" }}
                  >
                    No se pudo cargar la imagen
                  </div>
                  <a
                    href={comprobanteImgUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="absolute top-2 right-2 bg-white rounded-lg p-1.5 shadow text-gray-600 hover:text-gray-900"
                    title="Abrir en pestaña nueva"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-400 flex items-center gap-1">
              <Image className="h-3.5 w-3.5" />
              Sin pantallazo — el usuario no ha subido comprobante
            </p>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex flex-col gap-2 flex-shrink-0">
          <Button
            variant="primary"
            onClick={() => onApprove(payment)}
            disabled={disabled}
            className="whitespace-nowrap"
          >
            <CheckCircle className="h-4 w-4 mr-1" />
            Activar {payment.plan ? payment.plan.charAt(0).toUpperCase() + payment.plan.slice(1) : "plan"}
          </Button>
          <Button
            variant="secondary"
            onClick={() => onReject(payment)}
            disabled={disabled}
            className="whitespace-nowrap"
          >
            <XCircle className="h-4 w-4 mr-1" />
            Rechazar
          </Button>
        </div>
      </div>
    </Card>
  );
}
