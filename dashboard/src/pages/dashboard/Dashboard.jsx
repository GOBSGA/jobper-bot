import { useAuth } from "../../context/AuthContext";
import { useApi } from "../../hooks/useApi";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { money, date, relative } from "../../lib/format";
import {
  MagnifyingGlass,
  Lightning,
  Kanban,
  TrendUp,
  Bell,
  Star,
  Sparkle,
  Trophy,
  ArrowRight,
  Gift,
} from "@phosphor-icons/react";
import { Link } from "react-router-dom";

// KPI card with colored icon container
function KpiCard({ icon: Icon, iconBg, iconColor, label, value }) {
  return (
    <Card className="p-5 flex items-center gap-4">
      <div className={`flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-2xl ${iconBg}`}>
        <Icon size={20} weight="duotone" className={iconColor} />
      </div>
      <div className="min-w-0">
        <p className="text-2xs text-ink-400 uppercase tracking-wider font-medium">{label}</p>
        <p className="text-xl font-bold text-ink-900 tracking-tighter mt-0.5 leading-none">
          {value}
        </p>
      </div>
    </Card>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const { data: alerts, loading: alertsLoading } = useApi("/contracts/alerts?hours=24");
  const { data: matched, loading: matchedLoading } = useApi("/contracts/matched?limit=10&min_score=30");
  const { data: marketStats } = useApi("/contracts/market-stats");
  const isBusiness = ["competidor", "estratega", "dominador", "business", "enterprise"].includes(user?.plan);
  const isPaid = user?.plan && user.plan !== "free" && user.plan !== "trial";
  const { data: pipelineStats } = useApi(isBusiness ? "/pipeline/stats" : null);
  const { data: recs, loading: recsLoading } = useApi(isPaid ? "/contracts/recommendations" : null);

  const trialDays = user?.trial_ends_at
    ? Math.max(0, Math.ceil((new Date(user.trial_ends_at) - Date.now()) / 86400000))
    : 0;

  const name = user?.company_name || user?.email?.split("@")[0] || "tú";
  const initial = name[0]?.toUpperCase() || "?";
  const loading = alertsLoading || matchedLoading;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Buenos días" : hour < 18 ? "Buenas tardes" : "Buenas noches";

  return (
    <div className="space-y-6">

      {/* ── Greeting ─────────────────────────────────────────── */}
      <div className="flex items-center gap-4">
        <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-ink-900 text-white flex items-center justify-center text-lg font-bold tracking-tighter select-none">
          {initial}
        </div>
        <div>
          <h1 className="text-lg font-bold text-ink-900 tracking-snug leading-tight">
            {greeting}, {name}
          </h1>
          <p className="text-xs text-ink-400 mt-px">
            Plan <span className="capitalize font-medium text-ink-600">{user?.plan || "trial"}</span>
            {user?.plan === "trial" && trialDays > 0 && ` · ${trialDays} días de prueba restantes`}
          </p>
        </div>
      </div>

      {/* ── Notification banners ──────────────────────────────── */}
      {alerts?.count > 0 && (
        <div className="flex items-center gap-4 px-4 py-3.5 rounded-2xl bg-accent-50 border border-accent-200">
          <div className="flex items-center justify-center w-9 h-9 bg-accent-100 rounded-xl flex-shrink-0">
            <Bell size={18} weight="duotone" className="text-accent-700" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-accent-900 leading-tight">
              {alerts.count} {alerts.count === 1 ? "contrato nuevo" : "contratos nuevos"} para ti hoy
            </p>
            <p className="text-xs text-accent-700 mt-0.5">Publicados en las últimas 24 horas</p>
          </div>
          <Link
            to="/contracts"
            className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-accent-600 text-white rounded-xl text-xs font-semibold hover:bg-accent-700 transition-colors"
          >
            Ver <ArrowRight size={12} />
          </Link>
        </div>
      )}

      {user?.plan === "trial" && trialDays > 0 && trialDays <= 5 && (
        <div className="flex items-center gap-4 px-4 py-3.5 rounded-2xl bg-amber-50 border border-amber-200">
          <p className="text-sm text-amber-900 flex-1">
            <strong>Prueba gratis</strong> vence en {trialDays} días
          </p>
          <Link to="/payments">
            <Button size="sm">Ver planes</Button>
          </Link>
        </div>
      )}
      {user?.plan === "expired" && (
        <div className="flex items-center gap-4 px-4 py-3.5 rounded-2xl bg-red-50 border border-red-200">
          <p className="text-sm text-red-900 flex-1"><strong>Plan expirado</strong> — acceso limitado</p>
          <Link to="/payments"><Button size="sm">Renovar</Button></Link>
        </div>
      )}

      {/* ── KPI cards ────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard
          icon={MagnifyingGlass}
          iconBg="bg-brand-50"
          iconColor="text-brand-500"
          label="Totales"
          value={marketStats?.total_contracts?.toLocaleString() ?? "—"}
        />
        <KpiCard
          icon={Lightning}
          iconBg="bg-amber-50"
          iconColor="text-amber-500"
          label="Nuevos hoy"
          value={marketStats?.new_last_24h ?? "—"}
        />
        <KpiCard
          icon={Kanban}
          iconBg="bg-violet-50"
          iconColor="text-violet-500"
          label="Pipeline"
          value={pipelineStats?.total_entries ?? "—"}
        />
        <KpiCard
          icon={TrendUp}
          iconBg="bg-accent-50"
          iconColor="text-accent-600"
          label="Ganados"
          value={pipelineStats?.won_value ? money(pipelineStats.won_value) : "—"}
        />
      </div>

      {/* ── Sector insight ───────────────────────────────────── */}
      {marketStats?.sector_contracts_30d > 0 && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-brand-50 border border-brand-100">
          <Star size={16} weight="duotone" className="text-brand-500 flex-shrink-0" />
          <p className="text-sm text-brand-800 leading-snug">
            <strong>{marketStats.sector_contracts_30d} contratos</strong> en tu sector este mes
            {marketStats.sector_value_30d > 0 && <> · <strong>{money(marketStats.sector_value_30d)}</strong> en valor</>}
          </p>
        </div>
      )}

      {/* ── Matched feed ─────────────────────────────────────── */}
      <Card>
        <div className="flex items-center justify-between px-6 pt-5 pb-4">
          <div>
            <h2 className="text-sm font-bold text-ink-900 tracking-snug">Recomendados para ti</h2>
            <p className="text-2xs text-ink-400 mt-0.5">Basado en tu perfil y sector</p>
          </div>
          <Link
            to="/contracts"
            className="flex items-center gap-1 text-xs font-medium text-brand-500 hover:text-brand-700 transition-colors"
          >
            Ver todos <ArrowRight size={12} />
          </Link>
        </div>

        {loading ? (
          <div className="flex justify-center py-10"><Spinner /></div>
        ) : matched?.contracts?.length > 0 ? (
          <div className="divide-y divide-surface-border">
            {matched.contracts.map((c) => {
              const scoreColor =
                c.match_score >= 90 ? "bg-accent-50 text-accent-700" :
                c.match_score >= 80 ? "bg-brand-50 text-brand-600" :
                "bg-amber-50 text-amber-700";

              return (
                <Link
                  to={`/contracts/${c.id}`}
                  key={c.id}
                  className="flex items-start justify-between gap-4 px-6 py-3.5 hover:bg-surface-hover/50 transition-colors group"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-ink-900 truncate group-hover:text-brand-600 transition-colors">
                        {c.title}
                      </p>
                      {c.match_score >= 70 && (
                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded-md text-2xs font-bold ${scoreColor}`}>
                          {c.match_score}%
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-ink-400 mt-0.5 leading-tight">
                      {c.source} · {c.entity}
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0 space-y-1">
                    {c.amount && (
                      <p className="text-sm font-semibold text-ink-900">{money(c.amount)}</p>
                    )}
                    {c.deadline && (
                      <Badge color={new Date(c.deadline) < Date.now() ? "red" : "gray"}>
                        {relative(c.deadline)}
                      </Badge>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
        ) : (
          <div className="px-6 pb-6 text-center">
            <p className="text-sm text-ink-400">
              Configura tu perfil con keywords para ver contratos personalizados.
            </p>
            <Link
              to="/settings"
              className="inline-flex items-center gap-1 mt-2 text-xs font-medium text-brand-500 hover:text-brand-700"
            >
              Configurar perfil <ArrowRight size={11} />
            </Link>
          </div>
        )}
      </Card>

      {/* ── AI Recommendations ───────────────────────────────── */}
      {isPaid && (
        <Card>
          <div className="flex items-center justify-between px-6 pt-5 pb-4">
            <div className="flex items-center gap-2.5">
              <div className="flex items-center justify-center w-8 h-8 rounded-xl bg-violet-50">
                <Sparkle size={16} weight="duotone" className="text-violet-500" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-ink-900 tracking-snug">
                  Mejores oportunidades hoy
                </h2>
                {recs?.ai && (
                  <p className="text-[10px] text-violet-400 font-medium mt-px">IA · actualiza cada 24h</p>
                )}
              </div>
            </div>
          </div>

          {recsLoading ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : recs?.contracts?.length > 0 ? (
            <div className="px-4 pb-4 space-y-1.5">
              {recs.summary && (
                <p className="px-2 pb-2 text-xs text-ink-400 leading-relaxed border-b border-surface-border mb-3">
                  {recs.summary}
                </p>
              )}
              {recs.contracts.map((c, i) => (
                <Link
                  to={`/contracts/${c.id}`}
                  key={c.id}
                  className="flex items-start gap-3 px-3 py-3 rounded-xl hover:bg-surface-hover transition-colors group"
                >
                  {/* Rank badge */}
                  <div className={`flex-shrink-0 w-7 h-7 rounded-xl flex items-center justify-center text-xs font-bold ${
                    i === 0 ? "bg-amber-50 text-amber-600" :
                    i === 1 ? "bg-surface-hover text-ink-500" :
                    "bg-surface-hover text-ink-400"
                  }`}>
                    {i === 0 ? <Trophy size={14} weight="duotone" /> : i + 1}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-ink-900 group-hover:text-brand-600 transition-colors truncate">
                        {c.title}
                      </p>
                      {c.match_score > 0 && (
                        <span className="text-2xs font-semibold text-brand-500 bg-brand-50 px-1.5 py-0.5 rounded-md">
                          {c.match_score}%
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-ink-400 mt-0.5">{c.source} · {c.entity}</p>
                    {c.ai_reason && (
                      <p className="text-xs text-violet-500 mt-1 italic leading-snug">{c.ai_reason}</p>
                    )}
                  </div>

                  <div className="text-right flex-shrink-0 space-y-1">
                    {c.amount > 0 && (
                      <p className="text-sm font-semibold text-ink-900">{money(c.amount)}</p>
                    )}
                    {c.deadline && (
                      <Badge color={new Date(c.deadline) < Date.now() ? "red" : "gray"}>
                        {relative(c.deadline)}
                      </Badge>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="px-6 pb-6 text-center">
              <p className="text-sm text-ink-400">
                {recs?.summary || "Agrega keywords a tu perfil para ver recomendaciones IA."}
              </p>
              <Link to="/settings" className="inline-flex items-center gap-1 mt-2 text-xs font-medium text-brand-500 hover:text-brand-700">
                Configurar perfil <ArrowRight size={11} />
              </Link>
            </div>
          )}
        </Card>
      )}

      {/* ── Referral banner ──────────────────────────────────── */}
      <Card className="p-5">
        <div className="flex items-center gap-4">
          <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-2xl bg-ink-900">
            <Gift size={20} weight="duotone" className="text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-ink-900">Invita amigos, gana meses gratis</p>
            <p className="text-xs text-ink-400 mt-0.5">Invita 3 amigos y recibe 1 mes del plan Cazador gratis</p>
          </div>
          <Link to="/referrals" className="flex-shrink-0">
            <Button size="sm" variant="secondary">
              Invitar <ArrowRight size={12} />
            </Button>
          </Link>
        </div>
      </Card>

    </div>
  );
}
