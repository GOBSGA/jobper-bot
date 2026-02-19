import { useState } from "react";
import { Link } from "react-router-dom";
import { useApi } from "../../hooks/useApi";
import { api } from "../../lib/api";
import Card, { CardHeader } from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { useToast } from "../../components/ui/Toast";
import AdminKPIs from "../../components/admin/AdminKPIs";
import ContractMetrics from "../../components/admin/ContractMetrics";
import RecentActivity from "../../components/admin/RecentActivity";
import {
  Shield,
  Zap,
  AlertTriangle,
  RefreshCw,
  ClipboardCheck,
  Wifi,
  WifiOff,
} from "lucide-react";

function ServiceDot({ ok, label }) {
  return (
    <div className="flex items-center gap-2">
      {ok ? (
        <Wifi className="h-4 w-4 text-green-500" />
      ) : (
        <WifiOff className="h-4 w-4 text-red-500" />
      )}
      <span className="text-sm text-gray-700 capitalize">{label}</span>
      <Badge color={ok ? "green" : "red"}>{ok ? "OK" : "DOWN"}</Badge>
    </div>
  );
}

export default function Admin() {
  const toast = useToast();
  const [ingesting, setIngesting] = useState(false);

  const { data: kpis, loading, refetch: reload } = useApi("/admin/dashboard");
  const { data: health } = useApi("/admin/health");
  const { data: scrapers } = useApi("/admin/scrapers");

  const k = kpis || {};
  // health returns flat dict: { database, redis, openai, celery }
  const h = health || {};

  const triggerIngest = async () => {
    setIngesting(true);
    try {
      const res = await api.post("/admin/ingest", { days_back: 7 });
      toast.success(`Ingesta iniciada: ${res.message || "procesando..."}`);
    } catch (err) {
      toast.error(err.error || "Error al iniciar ingesta");
    } finally {
      setIngesting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }


  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-brand-600" />
          <h1 className="text-2xl font-bold text-gray-900">Panel de Control</h1>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={reload}>
            <RefreshCw className="h-4 w-4" /> Actualizar
          </Button>
          <Button size="sm" onClick={triggerIngest} disabled={ingesting}>
            <Zap className={`h-4 w-4 ${ingesting ? "animate-pulse" : ""}`} />
            {ingesting ? "Ingiriendo..." : "Ingerir contratos"}
          </Button>
          <Link to="/admin/payments">
            <Button size="sm" className="bg-amber-500 hover:bg-amber-600 relative">
              <ClipboardCheck className="h-4 w-4" />
              Revisar pagos
              {k.pending_payments > 0 && (
                <span className="absolute -top-1.5 -right-1.5 bg-red-500 text-white text-[10px] font-bold rounded-full h-4 w-4 flex items-center justify-center">
                  {k.pending_payments}
                </span>
              )}
            </Button>
          </Link>
        </div>
      </div>

      {/* Alerta de pagos pendientes */}
      {k.pending_payments > 0 && (
        <div className="bg-amber-50 border border-amber-300 rounded-xl p-4 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0" />
          <p className="text-sm text-amber-800 font-medium">
            {k.pending_payments} pago{k.pending_payments !== 1 ? "s" : ""} pendiente{k.pending_payments !== 1 ? "s" : ""} de revisión.{" "}
            <Link to="/admin/payments" className="underline font-bold">Revisar ahora →</Link>
          </p>
        </div>
      )}

      {/* KPIs */}
      <AdminKPIs kpis={k} />

      {/* Plan distribution + Contracts */}
      <ContractMetrics kpis={k} scrapers={scrapers} />

      {/* System health */}       <Card>
        <CardHeader title="Estado del sistema" subtitle="Servicios críticos de infraestructura" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <ServiceDot ok={h.database !== false} label="Base de datos" />
          <ServiceDot ok={!!h.redis} label="Redis / Cache" />
          <ServiceDot ok={!!h.openai} label="OpenAI API" />
          <ServiceDot ok={!!h.celery} label="Celery / Tasks" />
        </div>
        {!h.openai && health !== null && (
          <div className="mt-3 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-xs text-red-700 flex items-center gap-2">
            <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
            <span>
              <strong>OpenAI sin configurar:</strong> Establece la variable de entorno{" "}
              <code className="bg-red-100 px-1 rounded">OPENAI_API_KEY</code> en Railway para activar la verificación de comprobantes y análisis de contratos.
            </span>
          </div>
        )}
      </Card>

      {/* Recent activity */}
      <RecentActivity kpis={k} />
    </div>
  );
}
