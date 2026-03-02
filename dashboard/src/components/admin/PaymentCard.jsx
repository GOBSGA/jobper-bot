import { useState, useEffect } from "react";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import Spinner from "../ui/Spinner";
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

export const PLAN_LABELS = {
  free: "Free",
  alertas: "Alertas — $49,900",
  competidor: "Competidor — $149,900",
  cazador: "Cazador — $299,900",
  business: "Business — $499,900",
  dominador: "Dominador — $599,900",
};

const getStatusBadge = (status) => {
  switch (status) {
    case "grace":
      return <Badge color="green"><CheckCircle className="h-3 w-3 mr-1" />Gracia 24h</Badge>;
    case "review":
      return <Badge color="yellow"><Clock className="h-3 w-3 mr-1" />Revisión manual</Badge>;
    case "pending":
      return <Badge color="gray"><Clock className="h-3 w-3 mr-1" />Pendiente</Badge>;
    case "approved":
      return <Badge color="green"><CheckCircle className="h-3 w-3 mr-1" />Aprobado</Badge>;
    case "rejected":
      return <Badge color="red"><XCircle className="h-3 w-3 mr-1" />Rechazado</Badge>;
    default:
      return <Badge color="gray">{status}</Badge>;
  }
};

/** Fetches image with auth token and returns an object URL */
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
    <div className="flex items-center justify-center h-40 bg-gray-50 rounded-lg">
      <Spinner className="h-6 w-6" />
    </div>
  );
  if (error || !src) return (
    <div className="flex items-center justify-center h-24 bg-gray-50 rounded-lg text-sm text-gray-400">
      No se pudo cargar el comprobante
    </div>
  );
  return (
    <img
      src={src}
      alt="Comprobante de pago"
      className={className}
    />
  );
}

/**
 * Individual payment card for admin review
 */
export default function PaymentCard({ payment, onApprove, onReject, disabled }) {
  const [showImage, setShowImage] = useState(false);
  const hasComprobante = Boolean(payment.comprobante_url);
  const planLabel = PLAN_LABELS[payment.plan] || payment.plan || "—";
  const planName = payment.plan
    ? payment.plan.charAt(0).toUpperCase() + payment.plan.slice(1)
    : "Plan";

  return (
    <Card className="p-5">
      <div className="flex items-start gap-4">
        {/* Main content */}
        <div className="flex-1 space-y-4 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-xl font-bold text-gray-900">{money(payment.amount)}</span>
            {getStatusBadge(payment.status)}
            {payment.status === "grace" && (
              <span className="bg-green-100 text-green-800 text-xs font-bold px-2 py-0.5 rounded-full">
                ⚡ Acceso temporal activo
              </span>
            )}
          </div>

          {/* Details grid */}
          <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
            <div>
              <span className="text-gray-400">Usuario</span>
              <p className="font-medium text-gray-900">{payment.user_email}</p>
            </div>
            <div>
              <span className="text-gray-400">Plan a activar</span>
              <p className="font-semibold text-brand-700">{planLabel}</p>
            </div>
            <div>
              <span className="text-gray-400">Referencia</span>
              <p><code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">{payment.reference || "—"}</code></p>
            </div>
            <div>
              <span className="text-gray-400">Fecha</span>
              <p className="text-gray-700">{formatDate(payment.created_at)}</p>
            </div>
          </div>

          {/* AI verification */}
          {payment.verification && (
            <div className="p-3 bg-gray-50 rounded-lg space-y-2 text-xs">
              <p className="font-medium text-gray-700 flex items-center gap-1.5">
                <Eye className="h-3.5 w-3.5" /> Verificación IA
              </p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  ["Confianza", `${Math.round((payment.verification.confidence || 0) * 100)}%`],
                  ["Monto detectado", payment.verification.extracted_amount ? money(payment.verification.extracted_amount) : "—"],
                  ["Referencia detectada", payment.verification.extracted_reference || "—"],
                  ["Fecha detectada", payment.verification.extracted_date || "—"],
                ].map(([label, value]) => (
                  <div key={label}>
                    <span className="text-gray-400">{label}:</span>{" "}
                    <span className="font-medium">{value}</span>
                  </div>
                ))}
              </div>
              {payment.verification.issues?.length > 0 && (
                <div className="mt-1 text-amber-700">
                  <AlertTriangle className="h-3 w-3 inline mr-1" />
                  {payment.verification.issues.join(" · ")}
                </div>
              )}
            </div>
          )}

          {/* Comprobante */}
          {hasComprobante ? (
            <div className="space-y-2">
              <button
                onClick={() => setShowImage((v) => !v)}
                className="flex items-center gap-2 text-sm font-medium text-brand-600 hover:text-brand-800"
              >
                <Image className="h-4 w-4" />
                {showImage ? "Ocultar pantallazo" : "Ver pantallazo del cliente"}
              </button>
              {showImage && (
                <div className="rounded-xl overflow-hidden border border-gray-200 shadow-sm">
                  <AuthImage
                    paymentId={payment.id}
                    className="w-full max-h-[480px] object-contain bg-gray-50"
                  />
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-400 flex items-center gap-1.5">
              <Image className="h-3.5 w-3.5" />
              El usuario no ha subido pantallazo todavía
            </p>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex flex-col gap-2 flex-shrink-0 pt-1">
          <Button
            variant="primary"
            onClick={() => onApprove(payment)}
            disabled={disabled}
            className="whitespace-nowrap text-sm"
          >
            <CheckCircle className="h-4 w-4 mr-1" />
            Activar {planName}
          </Button>
          <Button
            variant="secondary"
            onClick={() => onReject(payment)}
            disabled={disabled}
            className="whitespace-nowrap text-sm"
          >
            <XCircle className="h-4 w-4 mr-1" />
            Rechazar
          </Button>
        </div>
      </div>
    </Card>
  );
}
