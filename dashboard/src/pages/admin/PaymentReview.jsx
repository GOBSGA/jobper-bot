import { useState, useEffect } from "react";
import { api } from "../../lib/api";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { useToast } from "../../components/ui/Toast";
import PaymentCard from "../../components/admin/PaymentCard";
import ApprovalModal from "../../components/admin/ApprovalModal";
import RejectModal from "../../components/admin/RejectModal";
import {
  Shield,
  CheckCircle,
  RefreshCw,
  AlertTriangle,
} from "lucide-react";

export default function PaymentReview() {
  const toast = useToast();
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [batchLoading, setBatchLoading] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [showApproveModal, setShowApproveModal] = useState(false);

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

  const handleBatchApprove = async () => {
    if (!window.confirm(
      `¿Aprobaste TODOS los pagos de hoy en tu Bre-B?\n\nEsto activará ${payments.length} plan(es). Solo confirma si ya verificaste que el dinero llegó.`
    )) return;
    setBatchLoading(true);
    try {
      const data = await api.post("/admin/payments/approve-all-today");
      toast.success(`✅ ${data.approved} pago(s) aprobado(s)${data.skipped?.length ? ` — ${data.skipped.length} omitido(s)` : ""}`);
      fetchPayments();
    } catch (err) {
      toast.error(err.error || "Error en aprobación masiva");
    } finally {
      setBatchLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();
  }, []);

  const openApproveModal = (payment) => {
    setSelected(payment);
    setShowApproveModal(true);
  };

  const handleApprove = async () => {
    if (!selected) return;
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

  const openRejectModal = (payment) => {
    setSelected(payment);
    setShowRejectModal(true);
  };

  const handleReject = async (reason) => {
    if (!selected) return;
    setActionLoading(true);
    try {
      await api.post(`/admin/payments/${selected.id}/reject`, { reason });
      toast.success("Pago rechazado");
      setShowRejectModal(false);
      setSelected(null);
      fetchPayments();
    } catch (err) {
      toast.error(err.error || "Error rechazando pago");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-brand-600" />
          <h1 className="text-2xl font-bold text-gray-900">Revisión de Pagos</h1>
          {payments.length > 0 && (
            <span className="bg-red-100 text-red-700 text-xs font-bold px-2 py-0.5 rounded-full">
              {payments.length} pendiente{payments.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          {payments.length > 0 && (
            <Button
              onClick={handleBatchApprove}
              disabled={batchLoading}
              className="bg-green-600 hover:bg-green-700"
            >
              <CheckCircle className={`h-4 w-4 mr-2 ${batchLoading ? "animate-spin" : ""}`} />
              Aprobar todos hoy ({payments.length})
            </Button>
          )}
          <Button variant="secondary" onClick={fetchPayments} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Actualizar
          </Button>
        </div>
      </div>

      {/* Warning banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-amber-800">Antes de aprobar cada pago:</p>
            <ol className="text-sm text-amber-700 mt-1 list-decimal list-inside space-y-0.5">
              <li>Abre tu app Bre-B (o Nequi) y busca el pago del día</li>
              <li>Verifica que el dinero <strong>realmente llegó</strong> a tu cuenta</li>
              <li>Confirma que el monto y la referencia coinciden</li>
              <li>Solo entonces haz clic en <strong>Aprobar</strong></li>
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
            <PaymentCard
              key={payment.id}
              payment={payment}
              onApprove={openApproveModal}
              onReject={openRejectModal}
              disabled={actionLoading}
            />
          ))}
        </div>
      )}

      {/* Approve Modal */}
      {showApproveModal && selected && (
        <ApprovalModal
          payment={selected}
          onConfirm={handleApprove}
          onCancel={() => setShowApproveModal(false)}
          loading={actionLoading}
        />
      )}


      {/* Reject Modal */}
      {showRejectModal && selected && (
        <RejectModal
          payment={selected}
          onConfirm={handleReject}
          onCancel={() => setShowRejectModal(false)}
          loading={actionLoading}
        />
      )}
    </div>
  );
}
