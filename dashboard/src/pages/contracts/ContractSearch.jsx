import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import { useGate, usePlanLimits } from "../../hooks/useGate";
import { FomoBanner, LockedInline } from "../../components/ui/LockedContent";
import { money, date, relative, truncate } from "../../lib/format";
import {
  Search,
  FileText,
  Zap,
  List,
  Lock,
  TrendingUp,
  Sparkles,
  Eye,
  Star,
} from "lucide-react";

export default function ContractSearch() {
  const [tab, setTab] = useState("para_ti"); // "para_ti" | "todos"
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [matched, setMatched] = useState(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [showFomoBanner, setShowFomoBanner] = useState(true);

  const { isFreeTier, limits } = usePlanLimits();
  const scoreGate = useGate("match_scores");
  const navigate = useNavigate();

  const searchAll = async (p = 1) => {
    setLoading(true);
    try {
      const data = await api.get(
        `/contracts/search?query=${encodeURIComponent(query)}&page=${p}&per_page=20`
      );
      setResults(data);
      setPage(p);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  const loadMatched = async () => {
    setLoading(true);
    try {
      const data = await api.get("/contracts/matched?limit=50&min_score=20");
      setMatched(data);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMatched();
  }, []);

  useEffect(() => {
    if (tab === "todos" && !results) searchAll();
  }, [tab]);

  const handleSearch = (e) => {
    e.preventDefault();
    setTab("todos");
    searchAll();
  };

  // Calcular estadísticas de FOMO
  const highMatchCount = matched?.contracts?.filter((c) => c.match_score >= 70).length || 0;
  const totalMatched = matched?.contracts?.length || 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Contratos</h1>

      {/* FOMO Banner para usuarios Free */}
      {isFreeTier && showFomoBanner && highMatchCount > 0 && (
        <FomoBanner
          count={highMatchCount}
          feature="match_scores"
          requiredPlan="cazador"
          message={`${highMatchCount} contratos tienen 70%+ de compatibilidad contigo — ve los detalles`}
          onDismiss={() => setShowFomoBanner(false)}
        />
      )}

      <form onSubmit={handleSearch} className="flex gap-3">
        <Input
          className="flex-1"
          placeholder="Buscar: software, construcción, consultoría..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit" disabled={loading}>
          <Search className="h-4 w-4" /> Buscar
        </Button>
      </form>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => setTab("para_ti")}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition ${
            tab === "para_ti"
              ? "bg-white text-brand-700 shadow-sm"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          <Zap className="h-4 w-4" /> Para ti
          {totalMatched > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-brand-100 text-brand-700 rounded-full">
              {totalMatched}
            </span>
          )}
        </button>
        <button
          onClick={() => setTab("todos")}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition ${
            tab === "todos"
              ? "bg-white text-brand-700 shadow-sm"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          <List className="h-4 w-4" /> Todos
        </button>
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      )}

      {/* Para ti tab */}
      {tab === "para_ti" && !loading && (
        <>
          {matched?.contracts?.length > 0 ? (
            <>
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  {matched.contracts.length} contratos recomendados según tu perfil
                </p>
                {isFreeTier && (
                  <button
                    onClick={() => navigate("/payments?plan=cazador")}
                    className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                  >
                    <Sparkles className="h-3 w-3" />
                    Ver match scores reales
                  </button>
                )}
              </div>

              {/* Stats cards for FOMO */}
              {isFreeTier && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-3 text-center border border-green-200">
                    <div className="flex items-center justify-center gap-1 text-green-700">
                      <TrendingUp className="h-4 w-4" />
                      <span className="text-lg font-bold">
                        {scoreGate.allowed ? (
                          matched.contracts.filter((c) => c.match_score >= 85).length
                        ) : (
                          <span className="inline-flex items-center gap-1">
                            <Lock className="h-3 w-3" />?
                          </span>
                        )}
                      </span>
                    </div>
                    <p className="text-xs text-green-600 mt-1">85%+ match</p>
                  </div>
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-3 text-center border border-blue-200">
                    <div className="flex items-center justify-center gap-1 text-blue-700">
                      <Eye className="h-4 w-4" />
                      <span className="text-lg font-bold">
                        {scoreGate.allowed ? (
                          matched.contracts.filter((c) => c.match_score >= 70).length
                        ) : (
                          <span className="inline-flex items-center gap-1">
                            <Lock className="h-3 w-3" />?
                          </span>
                        )}
                      </span>
                    </div>
                    <p className="text-xs text-blue-600 mt-1">70%+ match</p>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-3 text-center border border-purple-200">
                    <div className="flex items-center justify-center gap-1 text-purple-700">
                      <Star className="h-4 w-4" />
                      <span className="text-lg font-bold">{matched.contracts.length}</span>
                    </div>
                    <p className="text-xs text-purple-600 mt-1">Total</p>
                  </div>
                </div>
              )}

              <div className="space-y-3">
                {matched.contracts.map((c) => (
                  <ContractCard key={c.id} c={c} showScore />
                ))}
              </div>
            </>
          ) : (
            <EmptyState
              icon={Zap}
              title="Configura tu perfil para ver recomendaciones"
              description="Ve a Configuración y agrega tu sector, palabras clave y ciudad. Jobper encontrará los contratos perfectos para ti."
            />
          )}
        </>
      )}

      {/* Todos tab */}
      {tab === "todos" && !loading && results && (
        <>
          <p className="text-sm text-gray-500">{results.total} contratos</p>
          {results.contracts?.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="Sin resultados"
              description="Intenta con otras palabras clave."
            />
          ) : (
            <div className="space-y-3">
              {results.contracts.map((c) => (
                <ContractCard key={c.id} c={c} />
              ))}
            </div>
          )}

          {results.total > 20 && (
            <div className="flex justify-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => searchAll(page - 1)}
              >
                Anterior
              </Button>
              <span className="text-sm text-gray-500 py-1.5">
                Página {page} de {results.pages}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={results.contracts?.length < 20}
                onClick={() => searchAll(page + 1)}
              >
                Siguiente
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// =============================================================================
// CONTRACT CARD — Con FOMO para usuarios Free
// =============================================================================
function ContractCard({ c, showScore }) {
  const descGate = useGate("full_description");
  const scoreGate = useGate("match_scores");
  const amountGate = useGate("show_amount");
  const navigate = useNavigate();

  const handleLockedClick = (e, feature, plan) => {
    e.preventDefault();
    e.stopPropagation();
    navigate(`/payments?plan=${plan}&feature=${feature}`);
  };

  return (
    <Link to={`/contracts/${c.id}`}>
      <Card className="hover:shadow-md transition cursor-pointer group">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            {/* Title + Score */}
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-semibold text-gray-900 truncate max-w-md">
                {c.title}
              </h3>
              {showScore && c.match_score >= 50 && (
                <>
                  {scoreGate.allowed ? (
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold flex-shrink-0 ${
                        c.match_score >= 90
                          ? "bg-green-100 text-green-800"
                          : c.match_score >= 80
                          ? "bg-blue-100 text-blue-800"
                          : c.match_score >= 70
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {c.match_score}% match
                    </span>
                  ) : (
                    <button
                      onClick={(e) => handleLockedClick(e, "match_scores", "cazador")}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-600 hover:bg-blue-100 transition flex-shrink-0 border border-blue-200"
                      title="Desbloquea para ver tu % de compatibilidad"
                    >
                      <Lock className="h-3 w-3" />
                      <span className="animate-pulse">??%</span>
                      <Sparkles className="h-3 w-3" />
                    </button>
                  )}
                </>
              )}
            </div>

            {/* Entity + Source */}
            <p className="text-xs text-gray-500 mt-1">
              {c.entity} · {c.source}
            </p>

            {/* Description with FOMO */}
            {c.description && (
              <div className="mt-2">
                {descGate.allowed ? (
                  <p className="text-sm text-gray-600 line-clamp-2">{c.description}</p>
                ) : (
                  <div className="relative">
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {truncate(c.description, 120)}
                    </p>
                    {c.description.length > 120 && (
                      <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-white to-transparent" />
                    )}
                  </div>
                )}
              </div>
            )}

            {/* FOMO message for truncated description */}
            {c.description && !descGate.allowed && c.description.length > 120 && (
              <button
                onClick={(e) => handleLockedClick(e, "full_description", "cazador")}
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 mt-1 font-medium"
              >
                <Lock className="h-3 w-3" />
                Ver descripción completa
              </button>
            )}
          </div>

          {/* Right side: Amount, Badge, Deadline */}
          <div className="text-right flex-shrink-0 space-y-1">
            {/* Amount with FOMO */}
            {c.amount ? (
              amountGate.allowed ? (
                <p className="text-sm font-bold text-gray-900">{money(c.amount)}</p>
              ) : (
                <button
                  onClick={(e) => handleLockedClick(e, "show_amount", "cazador")}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded bg-gray-100 hover:bg-gray-200 transition text-gray-500 text-sm font-medium"
                  title="Desbloquea para ver el monto"
                >
                  <Lock className="h-3 w-3" />
                  $•••••
                </button>
              )
            ) : null}

            <Badge color={c.source?.includes("SECOP") ? "blue" : "purple"}>{c.source}</Badge>

            {c.deadline && (
              <p className="text-xs text-gray-500">{relative(c.deadline)}</p>
            )}
          </div>
        </div>

        {/* Hover hint for Free users */}
        {(!scoreGate.allowed || !descGate.allowed || !amountGate.allowed) && (
          <div className="mt-3 pt-3 border-t border-gray-100 opacity-0 group-hover:opacity-100 transition-opacity">
            <p className="text-xs text-gray-400 flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-blue-500" />
              Activa <span className="font-semibold text-blue-600">Cazador</span> para ver
              todos los detalles
            </p>
          </div>
        )}
      </Card>
    </Link>
  );
}
