import { useState, useEffect } from "react";
import { api } from "../../lib/api";
import Card, { CardHeader } from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import Modal from "../../components/ui/Modal";
import { useToast } from "../../components/ui/Toast";
import { money } from "../../lib/format";
import {
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  AlertTriangle,
  RefreshCw,
  CheckSquare,
  Square,
} from "lucide-react";

export default function PaymentReview() {
  const toast = useToast();
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [checklist, setChecklist] = useState({
    moneyReceived: false,
    amountCorrect: false,
    referenceMatch: false,
  });

  const fetchPayments = async () => {
    setLoading(true);
    try {
      const data = await api.get("/admin/payments/review");
      setPayments(data.payments || []);
    } catch (err) {
      toast.error(err.error || "Error cargando pagos pendientes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();
  }, []);

  const openApproveModal = (payment) => {
    setSelected(payment);
    setChecklist({ moneyReceived: false, amountCorrect: false, referenceMatch: false });
    setShowApproveModal(true);
  };

  const handleApprove = async () => {
    if (!selected) return;
    if (!checklist.moneyReceived || !checklist.amountCorrect || !checklist.referenceMatch) {
      toast.error("Debes confirmar todos los puntos del checklist");
      return;
    }

    setActionLoading(true);
    try {
      await api.post(`/admin/payments/${selected.id}/approve`);
      toast.success("Pago aprobado exitosamente");
      setShowApproveModal(false);
      setSelected(null);
      fetchPayments();
    } catch (err) {
      toast.error(err.error || "Error aprobando pago");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selected) return;
    setActionLoading(true);
    try {
      await api.post(`/admin/payments/${selected.id}/reject`, { reason: rejectReason });
      toast.success("Pago rechazado");
      setShowRejectModal(false);
      setSelected(null);
      setRejectReason("");
      fetchPayments();
    } catch (err) {
      toast.error(err.error || "Error rechazando pago");
    } finally {
      setActionLoading(false);
    }
  };

  const openRejectModal = (payment) => {
    setSelected(payment);
    setShowRejectModal(true);
  };

  const toggleChecklist = (key) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

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

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.7) return "text-green-600";
    if (confidence >= 0.4) return "text-yellow-600";
    return "text-red-600";
  };

  const allChecked = checklist.moneyReceived && checklist.amountCorrect && checklist.referenceMatch;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-brand-600" />
          <h1 className="text-2xl font-bold text-gray-900">Revisión de Pagos</h1>
        </div>
        <Button variant="secondary" onClick={fetchPayments} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Actualizar
        </Button>
      </div>

      {/* Warning banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-amber-800">Antes de aprobar un pago:</p>
            <ol className="text-sm text-amber-700 mt-1 list-decimal list-inside">
              <li>Abre tu app de Nequi/Bancolombia</li>
              <li>Verifica que el dinero REALMENTE llegó</li>
              <li>Confirma que el monto y referencia coinciden</li>
            </ol>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      ) : payments.length === 0 ? (
        <Card className="text-center py-12">
          <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900">Sin pagos pendientes</p>
          <p className="text-sm text-gray-500 mt-1">Todos los pagos han sido revisados.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {payments.map((payment) => (
            <Card key={payment.id} className="p-4">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold text-gray-900">
                      {money(payment.amount)}
                    </span>
                    {getStatusBadge(payment.status)}
                    {payment.verification_status && (
                      <Badge color="purple">{payment.verification_status}</Badge>
                    )}
                  </div>

                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Usuario:</strong> {payment.user_email} (ID: {payment.user_id})</p>
                    <p><strong>Plan:</strong> {payment.plan || "—"}</p>
                    <p><strong>Referencia:</strong> <code className="bg-gray-100 px-1 rounded">{payment.reference || "—"}</code></p>
                    <p><strong>Fecha:</strong> {formatDate(payment.created_at)}</p>
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
                          <span className={`ml-1 font-bold ${getConfidenceColor(payment.verification.confidence)}`}>
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
                  <Button
                    variant="primary"
                    onClick={() => openApproveModal(payment)}
                    disabled={actionLoading}
                  >
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Aprobar
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => openRejectModal(payment)}
                    disabled={actionLoading}
                  >
                    <XCircle className="h-4 w-4 mr-1" />
                    Rechazar
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Approve Modal with Checklist */}
      {showApproveModal && selected && (
        <Modal onClose={() => setShowApproveModal(false)}>
          <div className="p-6 space-y-4">
            <h3 className="text-lg font-bold text-gray-900">Confirmar Aprobación</h3>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                Aprobando pago de <strong>{money(selected.amount)}</strong> para{" "}
                <strong>{selected.user_email}</strong>
              </p>
              <p className="text-xs text-blue-600 mt-1">
                Referencia: <code className="bg-blue-100 px-1 rounded">{selected.reference}</code>
              </p>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <p className="font-medium text-amber-800 mb-3">
                Confirma que verificaste en tu Nequi/Bancolombia:
              </p>

              <div className="space-y-3">
                <button
                  onClick={() => toggleChecklist("moneyReceived")}
                  className="flex items-center gap-3 w-full text-left"
                >
                  {checklist.moneyReceived ? (
                    <CheckSquare className="h-5 w-5 text-green-600" />
                  ) : (
                    <Square className="h-5 w-5 text-gray-400" />
                  )}
                  <span className={checklist.moneyReceived ? "text-green-700" : "text-gray-700"}>
                    El dinero SÍ llegó a mi cuenta
                  </span>
                </button>

                <button
                  onClick={() => toggleChecklist("amountCorrect")}
                  className="flex items-center gap-3 w-full text-left"
                >
                  {checklist.amountCorrect ? (
                    <CheckSquare className="h-5 w-5 text-green-600" />
                  ) : (
                    <Square className="h-5 w-5 text-gray-400" />
                  )}
                  <span className={checklist.amountCorrect ? "text-green-700" : "text-gray-700"}>
                    El monto es exactamente {money(selected.amount)}
                  </span>
                </button>

                <button
                  onClick={() => toggleChecklist("referenceMatch")}
                  className="flex items-center gap-3 w-full text-left"
                >
                  {checklist.referenceMatch ? (
                    <CheckSquare className="h-5 w-5 text-green-600" />
                  ) : (
                    <Square className="h-5 w-5 text-gray-400" />
                  )}
                  <span className={checklist.referenceMatch ? "text-green-700" : "text-gray-700"}>
                    La referencia coincide: <code className="bg-amber-100 px-1 rounded text-xs">{selected.reference}</code>
                  </span>
                </button>
              </div>
            </div>

            <div className="flex gap-3 justify-end">
              <Button variant="secondary" onClick={() => setShowApproveModal(false)}>
                Cancelar
              </Button>
              <Button
                variant="primary"
                onClick={handleApprove}
                disabled={actionLoading || !allChecked}
                className={!allChecked ? "opacity-50 cursor-not-allowed" : ""}
              >
                {actionLoading ? (
                  <Spinner className="h-4 w-4" />
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Aprobar Pago
                  </>
                )}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Reject Modal */}
      {showRejectModal && selected && (
        <Modal onClose={() => setShowRejectModal(false)}>
          <div className="p-6 space-y-4">
            <h3 className="text-lg font-bold text-gray-900">Rechazar Pago</h3>
            <p className="text-sm text-gray-600">
              Rechazando pago de <strong>{money(selected.amount)}</strong> para{" "}
              <strong>{selected.user_email}</strong>
            </p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Razón del rechazo (se enviará al usuario)
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                rows={3}
                placeholder="Ej: El monto no coincide, la referencia no aparece, comprobante ilegible..."
              />
            </div>
            <div className="flex gap-3 justify-end">
              <Button variant="secondary" onClick={() => setShowRejectModal(false)}>
                Cancelar
              </Button>
              <Button
                variant="primary"
                className="bg-red-600 hover:bg-red-700"
                onClick={handleReject}
                disabled={actionLoading}
              >
                {actionLoading ? <Spinner className="h-4 w-4" /> : "Confirmar Rechazo"}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
