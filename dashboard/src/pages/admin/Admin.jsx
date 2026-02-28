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
import { date } from "../../lib/format";
import {
  ShieldCheck,
  Lightning,
  Warning,
  ArrowsClockwise,
  ClipboardText,
  WifiHigh,
  WifiSlash,
  ChartLine,
  Play,
} from "@phosphor-icons/react";

function ServiceDot({ ok, label }) {
  return (
    <div className="flex items-center gap-2">
      {ok ? (
        <WifiHigh size={16} className="text-accent-500" weight="fill" />
      ) : (
        <WifiSlash size={16} className="text-red-500" weight="fill" />
      )}
      <span className="text-sm text-ink-700 capitalize">{label}</span>
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
  const { data: activityData } = useApi("/admin/activity?per_page=15");
  const [triggeringScraper, setTriggeringScraper] = useState("");

  const k = kpis || {};
  const h = health || {};
  const activityFeed = activityData?.results || [];
  const scraperSources = scrapers?.sources || scrapers || [];

  const triggerScraper = async (sourceKey) => {
    setTriggeringScraper(sourceKey);
    try {
      const res = await api.post(`/admin/scrapers/${sourceKey}/trigger`);
      toast.success(res.message || `${sourceKey}: ingesta iniciada en segundo plano`);
      setTimeout(reload, 5000); // reload after 5s to show updated counts
    } catch (err) {
      toast.error(err.error || `Error al ejecutar ${sourceKey}`);
    } finally {
      setTriggeringScraper("");
    }
  };

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
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <ShieldCheck size={22} className="text-brand-600" weight="duotone" />
          <h1 className="text-xl sm:text-2xl font-bold text-ink-900">Panel de Control</h1>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button variant="secondary" size="sm" onClick={reload}>
            <ArrowsClockwise size={15} /> Actualizar
          </Button>
          <Button size="sm" onClick={triggerIngest} disabled={ingesting}>
            <Lightning size={15} className={ingesting ? "animate-pulse" : ""} />
            {ingesting ? "Ingiriendo..." : "Ingerir contratos"}
          </Button>
          <Link to="/admin/payments">
            <Button size="sm" className="bg-amber-500 hover:bg-amber-600 relative">
              <ClipboardText size={15} />
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

      {/* Pending payments alert */}
      {k.pending_payments > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3">
          <Warning size={18} className="text-amber-600 flex-shrink-0" weight="fill" />
          <p className="text-sm text-amber-800 font-medium">
            {k.pending_payments} pago{k.pending_payments !== 1 ? "s" : ""} pendiente
            {k.pending_payments !== 1 ? "s" : ""} de revisión.{" "}
            <Link to="/admin/payments" className="underline font-bold">
              Revisar ahora →
            </Link>
          </p>
        </div>
      )}

      {/* KPIs */}
      <AdminKPIs kpis={k} />

      {/* Plan distribution + Contracts */}
      <ContractMetrics kpis={k} scrapers={scraperSources} />

      {/* System health */}
      <Card className="p-5 sm:p-6">
        <CardHeader title="Estado del sistema" subtitle="Servicios críticos de infraestructura" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
          <ServiceDot ok={h.database !== false} label="Base de datos" />
          <ServiceDot ok={!!h.redis} label="Redis / Cache" />
          <ServiceDot ok={!!h.openai} label="OpenAI API" />
          <ServiceDot ok={!!h.celery} label="Celery / Tasks" />
        </div>
        {!h.openai && health !== null && (
          <div className="mt-3 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-xs text-red-700 flex items-center gap-2">
            <Warning size={13} className="flex-shrink-0" weight="fill" />
            <span>
              <strong>OpenAI sin configurar:</strong> Establece la variable de entorno{" "}
              <code className="bg-red-100 px-1 rounded">OPENAI_API_KEY</code> en Railway para
              activar la verificación de comprobantes y análisis de contratos.
            </span>
          </div>
        )}
      </Card>

      {/* Recent activity */}
      <RecentActivity kpis={k} />

      {/* Scrapers */}
      <Card className="p-5 sm:p-6">
        <CardHeader title="Scrapers" subtitle="Ejecutar manualmente una fuente" />
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 mt-4">
          {scraperSources.map((s) => (
            <button
              key={s.key}
              onClick={() => triggerScraper(s.key)}
              disabled={!!triggeringScraper}
              className={`flex items-center gap-2 px-3 py-2.5 rounded-xl border text-sm transition ${
                triggeringScraper === s.key
                  ? "border-brand-300 bg-brand-50 text-brand-700"
                  : "border-surface-border hover:border-brand-300 hover:bg-surface-hover text-ink-700"
              } disabled:opacity-50`}
            >
              {triggeringScraper === s.key ? (
                <ArrowsClockwise size={13} className="animate-spin text-brand-600 flex-shrink-0" />
              ) : (
                <Play size={13} className="text-ink-400 flex-shrink-0" weight="fill" />
              )}
              <span className="truncate">{s.name || s.key}</span>
            </button>
          ))}
        </div>
      </Card>

      {/* Global Activity Feed */}
      <Card className="p-5 sm:p-6">
        <div className="flex items-center gap-2 mb-4">
          <ChartLine size={18} className="text-purple-500" weight="duotone" />
          <div>
            <p className="font-semibold text-ink-900 text-sm">Feed de actividad</p>
            <p className="text-xs text-ink-400">Acciones recientes de todos los usuarios</p>
          </div>
        </div>
        {activityFeed.length === 0 ? (
          <p className="text-sm text-ink-400">Sin actividad registrada</p>
        ) : (
          <div className="space-y-0">
            {activityFeed.map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between text-sm py-2.5 border-b border-surface-border last:border-0"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="px-2 py-0.5 bg-surface-hover rounded-lg text-xs font-mono flex-shrink-0 text-ink-600">
                    {a.action}
                  </span>
                  <span className="text-ink-600 truncate max-w-[140px] sm:max-w-[200px]">
                    {a.user_email}
                  </span>
                  {a.resource && (
                    <span className="text-ink-400 text-xs truncate hidden sm:block">
                      {a.resource}
                      {a.resource_id ? ` #${a.resource_id}` : ""}
                    </span>
                  )}
                </div>
                <span className="text-xs text-ink-400 flex-shrink-0 ml-2">{date(a.created_at)}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
