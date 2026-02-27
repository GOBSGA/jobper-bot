import { useAuth } from "../../context/AuthContext";
import { useApi } from "../../hooks/useApi";
import Card, { CardHeader } from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { money, date, relative } from "../../lib/format";
import { Search, Heart, GitBranch, TrendingUp, Bell, Zap, Star, ChevronRight, Sparkles, Trophy } from "lucide-react";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const { user } = useAuth();
  const { data: alerts, loading: alertsLoading } = useApi("/contracts/alerts?hours=24");
  const { data: matched, loading: matchedLoading } = useApi("/contracts/matched?limit=10&min_score=30");
  const { data: marketStats } = useApi("/contracts/market-stats");
  const isBusiness = ["competidor", "dominador", "business", "enterprise"].includes(user?.plan);
  const isPaid = user?.plan && user.plan !== "free" && user.plan !== "trial";
  const { data: pipelineStats } = useApi(isBusiness ? "/pipeline/stats" : null);
  const { data: recs, loading: recsLoading } = useApi(isPaid ? "/contracts/recommendations" : null);

  const trialDays = user?.trial_ends_at
    ? Math.max(0, Math.ceil((new Date(user.trial_ends_at) - Date.now()) / 86400000))
    : 0;

  const loading = alertsLoading || matchedLoading;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Hola, {user?.company_name || user?.email?.split("@")[0]}
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Plan {user?.plan || "trial"}
          {user?.plan === "trial" && trialDays > 0 && ` — ${trialDays} días restantes`}
        </p>
      </div>

      {/* Alerts banner */}
      {alerts?.count > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-green-100 rounded-full">
              <Bell className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="font-semibold text-green-900">
                {alerts.count} {alerts.count === 1 ? "contrato nuevo" : "contratos nuevos"} para ti hoy
              </p>
              <p className="text-sm text-green-700">Contratos que coinciden con tu perfil publicados en las últimas 24 horas</p>
            </div>
          </div>
          <Link to="/contracts" className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 whitespace-nowrap">
            Ver contratos
          </Link>
        </div>
      )}

      {/* Plan warnings */}
      {user?.plan === "trial" && trialDays > 0 && trialDays <= 5 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center justify-between">
          <div>
            <p className="font-semibold text-yellow-900">Tu prueba gratis vence en {trialDays} días</p>
            <p className="text-sm text-yellow-700">Elige un plan para no perder acceso a contratos y alertas.</p>
          </div>
          <Link to="/payments" className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 whitespace-nowrap">
            Ver planes
          </Link>
        </div>
      )}
      {user?.plan === "expired" && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between">
          <div>
            <p className="font-semibold text-red-900">Tu plan ha expirado</p>
            <p className="text-sm text-red-700">Renueva ahora para seguir accediendo a todas las funcionalidades.</p>
          </div>
          <Link to="/payments" className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 whitespace-nowrap">
            Renovar
          </Link>
        </div>
      )}

      {/* Market stats + KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="flex items-center gap-4">
          <Search className="h-8 w-8 text-brand-600" />
          <div>
            <p className="text-xs text-gray-500">Contratos totales</p>
            <p className="text-lg font-bold text-gray-900">{marketStats?.total_contracts?.toLocaleString() ?? "—"}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <Zap className="h-8 w-8 text-yellow-500" />
          <div>
            <p className="text-xs text-gray-500">Nuevos hoy</p>
            <p className="text-lg font-bold text-gray-900">{marketStats?.new_last_24h ?? "—"}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <GitBranch className="h-8 w-8 text-purple-600" />
          <div>
            <p className="text-xs text-gray-500">En pipeline</p>
            <p className="text-lg font-bold text-gray-900">{pipelineStats?.total_entries ?? "—"}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <TrendingUp className="h-8 w-8 text-green-600" />
          <div>
            <p className="text-xs text-gray-500">Ganados</p>
            <p className="text-lg font-bold text-gray-900">{pipelineStats?.won_value ? money(pipelineStats.won_value) : "—"}</p>
          </div>
        </Card>
      </div>

      {/* Sector stats if available */}
      {marketStats?.sector_contracts_30d > 0 && (
        <Card className="bg-brand-50 border-brand-200">
          <div className="flex items-center gap-3">
            <Star className="h-6 w-6 text-brand-600" />
            <div>
              <p className="text-sm font-semibold text-brand-900">
                Tu sector tiene {marketStats.sector_contracts_30d} contratos activos
                {marketStats.sector_value_30d > 0 && ` por ${money(marketStats.sector_value_30d)}`}
              </p>
              <p className="text-xs text-brand-700">En los últimos 30 días</p>
            </div>
          </div>
        </Card>
      )}

      {/* Matched feed — the core of the product */}
      <Card>
        <CardHeader
          title="Contratos recomendados para ti"
          action={<Link to="/contracts" className="text-sm text-brand-600 hover:underline">Ver todos</Link>}
        />
        {loading ? (
          <div className="flex justify-center py-8"><Spinner /></div>
        ) : matched?.contracts?.length > 0 ? (
          <div className="divide-y divide-gray-100">
            {matched.contracts.map((c) => (
              <Link to={`/contracts/${c.id}`} key={c.id} className="block py-3 hover:bg-gray-50 -mx-6 px-6 transition">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-gray-900 truncate">{c.title}</p>
                      {c.match_score >= 70 && (
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${
                          c.match_score >= 90 ? "bg-green-100 text-green-800" :
                          c.match_score >= 80 ? "bg-blue-100 text-blue-800" :
                          "bg-yellow-100 text-yellow-800"
                        }`}>
                          {c.match_score}%
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{c.source} · {c.entity}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    {c.amount && <p className="text-sm font-semibold text-gray-900">{money(c.amount)}</p>}
                    {c.deadline && (
                      <Badge color={new Date(c.deadline) < Date.now() ? "red" : "blue"}>
                        {relative(c.deadline)}
                      </Badge>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center">
            <p className="text-sm text-gray-500">Configura tu perfil con keywords y sector para ver recomendaciones personalizadas.</p>
            <Link to="/settings" className="inline-flex items-center gap-1 mt-2 text-sm text-brand-600 hover:underline">
              Configurar perfil <ChevronRight className="h-3 w-3" />
            </Link>
          </div>
        )}
      </Card>

      {/* AI Recommendations — paid users only */}
      {isPaid && (
        <Card>
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-500" />
                Tus mejores oportunidades hoy
              </span>
            }
            action={
              recs?.ai && (
                <span className="text-xs text-purple-500 font-medium flex items-center gap-1">
                  <Sparkles className="h-3 w-3" /> IA · actualiza cada 24h
                </span>
              )
            }
          />
          {recsLoading ? (
            <div className="flex justify-center py-6"><Spinner /></div>
          ) : recs?.contracts?.length > 0 ? (
            <div className="space-y-3">
              {recs.summary && (
                <p className="text-sm text-gray-500 pb-1 border-b border-gray-100">{recs.summary}</p>
              )}
              {recs.contracts.map((c, i) => (
                <Link to={`/contracts/${c.id}`} key={c.id} className="flex items-start gap-3 p-3 rounded-xl hover:bg-gray-50 transition -mx-2 px-2">
                  <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                    i === 0 ? "bg-yellow-100 text-yellow-700" :
                    i === 1 ? "bg-gray-100 text-gray-600" :
                    "bg-orange-50 text-orange-500"
                  }`}>
                    {i === 0 ? <Trophy className="h-4 w-4" /> : i + 1}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-gray-900 truncate">{c.title}</p>
                      {c.match_score > 0 && (
                        <span className="text-xs font-semibold text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded-full">
                          {c.match_score}%
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">{c.source} · {c.entity}</p>
                    {c.ai_reason && (
                      <p className="text-xs text-purple-700 mt-1 italic">{c.ai_reason}</p>
                    )}
                  </div>
                  <div className="text-right flex-shrink-0">
                    {c.amount > 0 && <p className="text-sm font-semibold text-gray-900">{money(c.amount)}</p>}
                    {c.deadline && (
                      <Badge color={new Date(c.deadline) < Date.now() ? "red" : "blue"}>
                        {relative(c.deadline)}
                      </Badge>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="py-6 text-center">
              <p className="text-sm text-gray-500">
                {recs?.summary || "Agrega palabras clave a tu perfil para ver recomendaciones IA."}
              </p>
              <Link to="/settings" className="inline-flex items-center gap-1 mt-2 text-sm text-brand-600 hover:underline">
                Configurar perfil <ChevronRight className="h-3 w-3" />
              </Link>
            </div>
          )}
          {!isPaid && (
            <div className="py-6 text-center">
              <p className="text-sm text-gray-500">Actualiza tu plan para ver las mejores oportunidades analizadas con IA.</p>
              <Link to="/payments" className="inline-flex items-center gap-1 mt-2 text-sm text-brand-600 hover:underline">
                Ver planes <ChevronRight className="h-3 w-3" />
              </Link>
            </div>
          )}
        </Card>
      )}

      {/* Referral banner */}
      <Card className="bg-gradient-to-r from-brand-50 to-purple-50 border-brand-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-semibold text-gray-900">Invita amigos y gana meses gratis</p>
            <p className="text-sm text-gray-600">Invita 3 amigos y recibe 1 mes del plan Alertas gratis</p>
          </div>
          <Link to="/referrals" className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 whitespace-nowrap">
            Invitar
          </Link>
        </div>
      </Card>
    </div>
  );
}
