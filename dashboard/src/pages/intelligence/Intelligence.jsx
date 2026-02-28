import { useState, useCallback } from "react";
import { useAuth } from "../../context/AuthContext";
import { useApi } from "../../hooks/useApi";
import { useGate } from "../../hooks/useGate";
import Card, { CardHeader } from "../../components/ui/Card";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import UpgradePrompt from "../../components/ui/UpgradePrompt";
import { money } from "../../lib/format";
import { ChartBar, Buildings, TrendUp, Stack } from "@phosphor-icons/react";

// ─── Pure-CSS chart components ───────────────────────────────────────────────

function HorizontalBar({ label, count, totalValue, maxCount }) {
  const pct = maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="w-40 text-xs text-ink-700 truncate flex-shrink-0" title={label}>
        {label}
      </span>
      <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
        <div
          className="bg-brand-500 h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-ink-900 w-8 text-right flex-shrink-0">
        {count}
      </span>
      <span className="text-xs text-ink-400 w-24 text-right flex-shrink-0">
        {money(totalValue)}
      </span>
    </div>
  );
}

function MonthlyBars({ data }) {
  if (!data || data.length === 0) return null;
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="flex items-end gap-1.5 h-28 pt-2">
      {data.map((d) => {
        const heightPct = Math.max((d.count / maxCount) * 100, 3);
        const label = d.period.substring(0, 7); // "2025-03"
        const monthLabel = new Date(d.period + "-01").toLocaleDateString("es", { month: "short" });
        return (
          <div key={d.period} className="flex-1 flex flex-col items-center gap-1 group relative min-w-0">
            {/* Tooltip */}
            <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 bg-ink-900 text-white text-[10px] rounded px-1.5 py-1 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
              {d.count} contratos
            </div>
            <div
              className="w-full bg-brand-500 rounded-t-sm hover:bg-brand-600 transition-colors cursor-default"
              style={{ height: `${heightPct}%` }}
            />
            <span className="text-[9px] text-ink-400 truncate w-full text-center">{monthLabel}</span>
          </div>
        );
      })}
    </div>
  );
}

function SourceBar({ source, count, totalValue, totalContracts }) {
  const pct = totalContracts > 0 ? Math.round((count / totalContracts) * 100) : 0;
  const sourceLabels = {
    secop: "SECOP II",
    secop1: "SECOP I",
    secop_adjudicados: "SECOP Adjudicados",
    ejecucion: "SECOP Ejecución",
    tvec: "Tienda Virtual",
    mercado_publico: "Mercado Público CL",
    compranet: "CompraNet MX",
    ecopetrol: "Ecopetrol",
  };
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="w-36 text-xs text-ink-700 truncate flex-shrink-0">
        {sourceLabels[source] || source}
      </span>
      <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
        <div
          className="bg-accent-500 h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-ink-400 w-8 text-right flex-shrink-0">{pct}%</span>
      <span className="text-xs font-semibold text-ink-900 w-8 text-right flex-shrink-0">{count}</span>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function Intelligence() {
  const { user } = useAuth();
  const { allowed, requiredPlan } = useGate("competitive_intelligence");

  const [keywords, setKeywords] = useState(user?.keywords || "");
  const [months, setMonths] = useState(12);
  const [submitted, setSubmitted] = useState({ keywords: user?.keywords || "", months: 12 });

  const apiPath = `/intelligence/market?keywords=${encodeURIComponent(submitted.keywords)}&months=${submitted.months}`;
  const { data, loading, refetch } = useApi(allowed ? apiPath : null);

  const handleSearch = (e) => {
    e.preventDefault();
    setSubmitted({ keywords, months });
  };

  if (!allowed) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Inteligencia competitiva</h1>
        <UpgradePrompt feature="competitive_intelligence" requiredPlan={requiredPlan}>
          <EmptyState
            icon={ChartBar}
            title="Inteligencia de mercado"
            description="Descubre qué entidades publican más contratos en tu sector, tendencias mensuales y distribución por fuente."
          />
        </UpgradePrompt>
      </div>
    );
  }

  const summary = data?.summary;
  const topEntities = data?.top_entities || [];
  const monthlyTrend = data?.monthly_trend || [];
  const bySource = data?.by_source || [];
  const maxEntityCount = topEntities.length > 0 ? Math.max(...topEntities.map((e) => e.count)) : 1;
  const totalContracts = bySource.reduce((s, r) => s + r.count, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Inteligencia competitiva</h1>
      </div>

      {/* Search bar */}
      <Card className="p-4">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="Palabras clave del sector (ej: software, construcción, consultoría)"
            className="flex-1 rounded-xl border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400 outline-none"
          />
          <select
            value={months}
            onChange={(e) => setMonths(Number(e.target.value))}
            className="rounded-xl border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500/20 outline-none bg-white"
          >
            <option value={3}>Últimos 3 meses</option>
            <option value={6}>Últimos 6 meses</option>
            <option value={12}>Últimos 12 meses</option>
            <option value={24}>Últimos 24 meses</option>
          </select>
          <button
            type="submit"
            className="px-5 py-2 rounded-xl bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 transition-colors flex items-center gap-1.5"
          >
            <ChartBar size={15} /> Analizar
          </button>
        </form>
      </Card>

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : !data ? (
        <EmptyState
          icon={ChartBar}
          title="Sin datos"
          description="Ingresa palabras clave para analizar el mercado en tu sector."
        />
      ) : (
        <>
          {/* Summary KPIs */}
          {summary && (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              <Card className="p-4 text-center">
                <p className="text-2xl font-bold text-ink-900">
                  {summary.total_contracts.toLocaleString("es")}
                </p>
                <p className="text-xs text-ink-400 mt-1">Contratos en el período</p>
              </Card>
              <Card className="p-4 text-center">
                <p className="text-2xl font-bold text-green-600">
                  {money(summary.total_value)}
                </p>
                <p className="text-xs text-ink-400 mt-1">Valor total publicado</p>
              </Card>
              <Card className="p-4 text-center col-span-2 lg:col-span-1">
                <p className="text-2xl font-bold text-brand-600">
                  {money(summary.avg_amount)}
                </p>
                <p className="text-xs text-ink-400 mt-1">Promedio por contrato</p>
              </Card>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top entities */}
            <Card className="p-5">
              <CardHeader title="Top entidades por actividad">
                <span className="text-xs text-ink-400">por nº de contratos</span>
              </CardHeader>
              {topEntities.length === 0 ? (
                <p className="text-sm text-ink-400 py-4 text-center">Sin datos para estos filtros.</p>
              ) : (
                <div className="space-y-0.5">
                  {topEntities.map((e, i) => (
                    <HorizontalBar
                      key={i}
                      label={e.entity}
                      count={e.count}
                      totalValue={e.total_value}
                      maxCount={maxEntityCount}
                    />
                  ))}
                </div>
              )}
            </Card>

            {/* Monthly trend */}
            <Card className="p-5">
              <CardHeader title="Tendencia mensual">
                <span className="text-xs text-ink-400">últimos {submitted.months} meses</span>
              </CardHeader>
              {monthlyTrend.length === 0 ? (
                <p className="text-sm text-ink-400 py-4 text-center">Sin datos.</p>
              ) : (
                <MonthlyBars data={monthlyTrend} />
              )}
              {monthlyTrend.length > 0 && (
                <div className="flex justify-between mt-3 text-xs text-ink-400">
                  <span>{monthlyTrend[0]?.period}</span>
                  <span>{monthlyTrend[monthlyTrend.length - 1]?.period}</span>
                </div>
              )}
            </Card>
          </div>

          {/* By source */}
          {bySource.length > 0 && (
            <Card className="p-5">
              <CardHeader title="Distribución por fuente" />
              <div className="space-y-0.5">
                {bySource.map((s, i) => (
                  <SourceBar
                    key={i}
                    source={s.source}
                    count={s.count}
                    totalValue={s.total_value}
                    totalContracts={totalContracts}
                  />
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
