import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import { getAccessToken } from "../../lib/storage";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import { SkeletonContractCard } from "../../components/ui/Skeleton";
import EmptyState from "../../components/ui/EmptyState";
import { useGate, usePlanLimits } from "../../hooks/useGate";
import { FomoBanner, LockedInline } from "../../components/ui/LockedContent";
import { useToast } from "../../components/ui/Toast";
import { money, date, relative, truncate } from "../../lib/format";
import {
  MagnifyingGlass,
  FileText,
  Lightning,
  List,
  Lock,
  TrendUp,
  Sparkle,
  Eye,
  Star,
  DownloadSimple,
  Spinner as PhosphorSpinner,
  BookmarkSimple,
  BellRinging,
  Trash,
} from "@phosphor-icons/react";

export default function ContractSearch() {
  const [tab, setTab] = useState("para_ti"); // "para_ti" | "todos"
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [matched, setMatched] = useState(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [showFomoBanner, setShowFomoBanner] = useState(true);
  const [searchError, setSearchError] = useState(null);
  const [savedSearches, setSavedSearches] = useState([]);
  const [savingSearch, setSavingSearch] = useState(false);

  const { isFreeTier, limits } = usePlanLimits();
  const scoreGate = useGate("match_scores");
  const exportGate = useGate("export");
  const savedSearchGate = useGate("saved_searches");
  const navigate = useNavigate();
  const [exporting, setExporting] = useState(false);
  const toast = useToast();

  const handleExport = async () => {
    setExporting(true);
    try {
      const params = new URLSearchParams({ query, limit: "200" });
      const BASE = import.meta.env.VITE_API_URL || "/api";
      const res = await fetch(`${BASE}/contracts/export?${params}`, {
        headers: { Authorization: `Bearer ${getAccessToken()}` },
      });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "contratos_jobper.xlsx";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silent — user sees nothing downloaded
    } finally {
      setExporting(false);
    }
  };

  const searchAll = async (p = 1) => {
    setLoading(true);
    setSearchError(null);
    try {
      const data = await api.get(
        `/contracts/search?query=${encodeURIComponent(query)}&page=${p}&per_page=20`
      );
      setResults(data);
      setPage(p);
    } catch (err) {
      setSearchError(err?.error || "Error al buscar contratos. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  const loadMatched = async () => {
    setLoading(true);
    setSearchError(null);
    try {
      const data = await api.get("/contracts/matched?limit=50&min_score=20");
      setMatched(data);
    } catch (err) {
      setSearchError(err?.error || "Error cargando contratos. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  const loadSavedSearches = async () => {
    if (!savedSearchGate.allowed) return;
    try {
      const data = await api.get("/contracts/saved-searches");
      setSavedSearches(Array.isArray(data) ? data : []);
    } catch {
      // silent
    }
  };

  const saveSearch = async () => {
    if (!savedSearchGate.allowed) {
      navigate(savedSearchGate.upgradeUrl);
      return;
    }
    const name = query.trim() || "Mi búsqueda";
    setSavingSearch(true);
    try {
      await api.post("/contracts/saved-searches", { name, query: query.trim() });
      toast.success(`Búsqueda guardada: "${name}"`);
      loadSavedSearches();
    } catch (err) {
      toast.error(err.error || "Error al guardar búsqueda");
    } finally {
      setSavingSearch(false);
    }
  };

  const deleteSavedSearch = async (id) => {
    try {
      await api.delete(`/contracts/saved-searches/${id}`);
      setSavedSearches((prev) => prev.filter((s) => s.id !== id));
    } catch {
      toast.error("Error al eliminar");
    }
  };

  useEffect(() => {
    loadMatched();
    loadSavedSearches();
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
      <h1 className="text-2xl font-bold text-ink-900">Contratos</h1>

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

      {/* Error banner */}
      {searchError && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700 flex items-center justify-between gap-3">
          <span>{searchError}</span>
          <button
            onClick={() => tab === "para_ti" ? loadMatched() : searchAll()}
            className="px-3 py-1 rounded-lg bg-red-100 hover:bg-red-200 text-red-700 font-medium text-xs whitespace-nowrap transition"
          >
            Reintentar
          </button>
        </div>
      )}

      <form onSubmit={handleSearch} className="flex gap-3">
        <Input
          className="flex-1"
          placeholder="Buscar: software, construcción, consultoría..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit" disabled={loading}>
          <MagnifyingGlass size={16} /> Buscar
        </Button>
        {query.trim() && (
          <button
            type="button"
            onClick={saveSearch}
            disabled={savingSearch}
            title={savedSearchGate.allowed ? "Guardar esta búsqueda y recibir alertas" : savedSearchGate.fomoMessage}
            className="flex items-center gap-1 px-3 py-2 rounded-xl border border-surface-border text-ink-600 hover:border-brand-300 hover:text-brand-600 hover:bg-brand-50 transition text-sm"
          >
            <BookmarkSimple size={15} weight={savingSearch ? "fill" : "regular"} />
          </button>
        )}
        {exportGate.allowed ? (
          <Button type="button" variant="secondary" onClick={handleExport} disabled={exporting} title="Exportar a Excel">
            {exporting ? <PhosphorSpinner size={16} className="animate-spin" /> : <DownloadSimple size={16} />}
          </Button>
        ) : (
          <button
            type="button"
            onClick={() => navigate("/payments?feature=export")}
            title="Exportar a Excel (requiere plan Cazador)"
            className="flex items-center gap-1 px-3 py-2 rounded-xl border border-surface-border text-ink-400 hover:border-surface-border hover:bg-surface-hover transition text-sm"
          >
            <Lock size={14} /> <DownloadSimple size={16} />
          </button>
        )}
      </form>

      {/* Saved searches panel */}
      {savedSearchGate.allowed && savedSearches.length > 0 && (
        <div className="flex flex-wrap gap-2 items-center">
          <BellRinging size={14} className="text-brand-500 flex-shrink-0" weight="duotone" />
          <span className="text-xs text-ink-400 flex-shrink-0">Alertas activas:</span>
          {savedSearches.map((s) => (
            <div
              key={s.id}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-brand-50 border border-brand-100 text-xs text-brand-700 group"
            >
              <button
                onClick={() => { setQuery(s.query || s.name); setTab("todos"); searchAll(); }}
                className="font-medium hover:underline"
              >
                {s.name}
              </button>
              <button
                onClick={() => deleteSavedSearch(s.id)}
                className="opacity-0 group-hover:opacity-100 transition-opacity text-brand-400 hover:text-red-500"
              >
                <Trash size={11} weight="bold" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-surface-hover rounded-2xl p-1">
        <button
          onClick={() => setTab("para_ti")}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition ${
            tab === "para_ti"
              ? "bg-white text-brand-600 shadow-sm"
              : "text-ink-400 hover:text-ink-600"
          }`}
        >
          <Lightning size={16} weight={tab === "para_ti" ? "duotone" : "regular"} /> Para ti
          {totalMatched > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-brand-100 text-brand-700 rounded-full">
              {totalMatched}
            </span>
          )}
        </button>
        <button
          onClick={() => setTab("todos")}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition ${
            tab === "todos"
              ? "bg-white text-brand-600 shadow-sm"
              : "text-ink-400 hover:text-ink-600"
          }`}
        >
          <List size={16} weight={tab === "todos" ? "duotone" : "regular"} /> Todos
        </button>
      </div>

      {/* Skeleton loading state */}
      {loading && (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonContractCard key={i} />
          ))}
        </div>
      )}

      {/* Para ti tab */}
      {tab === "para_ti" && !loading && (
        <>
          {matched?.contracts?.length > 0 ? (
            <>
              <div className="flex items-center justify-between">
                <p className="text-sm text-ink-400">
                  {matched.contracts.length} contratos recomendados según tu perfil
                </p>
                {isFreeTier && (
                  <button
                    onClick={() => navigate("/payments?plan=cazador")}
                    className="text-xs text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1"
                  >
                    <Sparkle size={12} />
                    Ver match scores reales
                  </button>
                )}
              </div>

              {/* Stats cards for FOMO */}
              {isFreeTier && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-accent-50 border border-accent-100 rounded-xl p-3 text-center">
                    <div className="flex items-center justify-center gap-1 text-accent-700">
                      <TrendUp size={16} weight="duotone" />
                      <span className="text-lg font-bold">
                        {scoreGate.allowed ? (
                          matched.contracts.filter((c) => c.match_score >= 85).length
                        ) : (
                          <span className="inline-flex items-center gap-1">
                            <Lock size={12} />?
                          </span>
                        )}
                      </span>
                    </div>
                    <p className="text-xs text-accent-600 mt-1">85%+ match</p>
                  </div>
                  <div className="bg-brand-50 border border-brand-100 rounded-xl p-3 text-center">
                    <div className="flex items-center justify-center gap-1 text-brand-700">
                      <Eye size={16} weight="duotone" />
                      <span className="text-lg font-bold">
                        {scoreGate.allowed ? (
                          matched.contracts.filter((c) => c.match_score >= 70).length
                        ) : (
                          <span className="inline-flex items-center gap-1">
                            <Lock size={12} />?
                          </span>
                        )}
                      </span>
                    </div>
                    <p className="text-xs text-brand-600 mt-1">70%+ match</p>
                  </div>
                  <div className="bg-surface-hover border border-surface-border rounded-xl p-3 text-center">
                    <div className="flex items-center justify-center gap-1 text-ink-600">
                      <Star size={16} weight="duotone" />
                      <span className="text-lg font-bold">{matched.contracts.length}</span>
                    </div>
                    <p className="text-xs text-ink-400 mt-1">Total</p>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                {matched.contracts.map((c) => (
                  <ContractCard key={c.id} c={c} showScore />
                ))}
              </div>
            </>
          ) : (
            <EmptyState
              icon={Lightning}
              title="Configura tu perfil para ver recomendaciones"
              description="Ve a Configuración y agrega tu sector, palabras clave y ciudad. Jobper encontrará los contratos perfectos para ti."
            />
          )}
        </>
      )}

      {/* Todos tab */}
      {tab === "todos" && !loading && results && (
        <>
          <p className="text-sm text-ink-400">{results.total} contratos</p>
          {results.contracts?.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="Sin resultados"
              description="Intenta con otras palabras clave."
            />
          ) : (
            <div className="space-y-2">
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
              <span className="text-sm text-ink-400 py-1.5">
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

// Strip HTML tags from SECOP descriptions
function stripHtml(str) {
  return str?.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim() || "";
}

// =============================================================================
// CONTRACT CARD — Con FOMO para usuarios Free
// =============================================================================
function ContractCard({ c, showScore }) {
  const descGate = useGate("full_description");
  const scoreGate = useGate("match_scores");
  const amountGate = useGate("show_amount");
  const navigate = useNavigate();

  const cleanDesc = stripHtml(c.description);

  const handleLockedClick = (e, feature, plan) => {
    e.preventDefault();
    e.stopPropagation();
    navigate(`/payments?plan=${plan}&feature=${feature}`);
  };

  return (
    <Link to={`/contracts/${c.id}`}>
      <Card className="hover:shadow-md transition cursor-pointer group p-4 sm:p-5">
        {/* Top row: title + score pill + amount */}
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex items-start gap-2 flex-wrap">
              <h3 className="text-base font-semibold text-ink-900 leading-snug">
                {c.title}
              </h3>
              {showScore && c.match_score >= 50 && (
                scoreGate.allowed ? (
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold flex-shrink-0 mt-0.5 ${
                      c.match_score >= 90
                        ? "bg-accent-50 text-accent-700"
                        : c.match_score >= 80
                        ? "bg-brand-50 text-brand-600"
                        : c.match_score >= 70
                        ? "bg-amber-50 text-amber-700"
                        : "bg-surface-hover text-ink-600"
                    }`}
                  >
                    {c.match_score}% match
                  </span>
                ) : (
                  <button
                    onClick={(e) => handleLockedClick(e, "match_scores", "cazador")}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-brand-50 text-brand-600 hover:bg-brand-100 transition flex-shrink-0 border border-brand-200 mt-0.5"
                    title="Desbloquea para ver tu % de compatibilidad"
                  >
                    <Lock size={10} />
                    <span className="animate-pulse">??%</span>
                    <Sparkle size={10} />
                  </button>
                )
              )}
            </div>

            {/* Entity */}
            <p className="text-xs text-ink-400 mt-1 truncate">{c.entity}</p>
          </div>

          {/* Amount (top-right) */}
          <div className="text-right flex-shrink-0">
            {c.amount ? (
              amountGate.allowed ? (
                <p className="text-sm font-bold text-ink-900 whitespace-nowrap">{money(c.amount)}</p>
              ) : (
                <button
                  onClick={(e) => handleLockedClick(e, "show_amount", "cazador")}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-surface-hover hover:bg-surface-border transition text-ink-400 text-sm font-medium"
                  title="Desbloquea para ver el monto"
                >
                  <Lock size={11} />
                  $•••••
                </button>
              )
            ) : null}
          </div>
        </div>

        {/* Description */}
        {cleanDesc && (
          <div className="mt-3">
            {descGate.allowed ? (
              <p className="text-sm text-ink-600 line-clamp-2 leading-relaxed">{cleanDesc}</p>
            ) : (
              <div className="relative">
                <p className="text-sm text-ink-600 line-clamp-2 leading-relaxed">
                  {truncate(cleanDesc, 140)}
                </p>
                {cleanDesc.length > 140 && (
                  <div className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-white to-transparent" />
                )}
              </div>
            )}
          </div>
        )}

        {/* Footer row: source badge + deadline + locked hint */}
        <div className="mt-3 pt-3 border-t border-surface-border flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Badge color={c.source?.includes("SECOP") ? "blue" : "purple"}>{c.source}</Badge>
            {c.deadline && (
              <span className="text-xs text-ink-400">{relative(c.deadline)}</span>
            )}
          </div>

          {/* Locked hint OR unlock CTA */}
          {c.description && !descGate.allowed && cleanDesc.length > 140 ? (
            <button
              onClick={(e) => handleLockedClick(e, "full_description", "cazador")}
              className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700 font-medium whitespace-nowrap"
            >
              <Lock size={10} />
              Ver completo
            </button>
          ) : (!scoreGate.allowed || !amountGate.allowed) ? (
            <span className="text-xs text-ink-400 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Sparkle size={11} className="text-brand-500" />
              <span>Desbloquea con <span className="font-semibold text-brand-600">Cazador</span></span>
            </span>
          ) : null}
        </div>
      </Card>
    </Link>
  );
}
