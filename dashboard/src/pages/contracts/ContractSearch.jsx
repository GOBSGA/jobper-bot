import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import { useGate } from "../../hooks/useGate";
import { money, date, relative, truncate } from "../../lib/format";
import { Search, FileText, Zap, List, Lock } from "lucide-react";

export default function ContractSearch() {
  const [tab, setTab] = useState("para_ti"); // "para_ti" | "todos"
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [matched, setMatched] = useState(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);

  const searchAll = async (p = 1) => {
    setLoading(true);
    try {
      const data = await api.get(`/contracts/search?query=${encodeURIComponent(query)}&page=${p}&per_page=20`);
      setResults(data);
      setPage(p);
    } catch {} finally { setLoading(false); }
  };

  const loadMatched = async () => {
    setLoading(true);
    try {
      const data = await api.get("/contracts/matched?limit=50&min_score=20");
      setMatched(data);
    } catch {} finally { setLoading(false); }
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

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Contratos</h1>

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
            tab === "para_ti" ? "bg-white text-brand-700 shadow-sm" : "text-gray-500 hover:text-gray-700"
          }`}
        >
          <Zap className="h-4 w-4" /> Para ti
        </button>
        <button
          onClick={() => setTab("todos")}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition ${
            tab === "todos" ? "bg-white text-brand-700 shadow-sm" : "text-gray-500 hover:text-gray-700"
          }`}
        >
          <List className="h-4 w-4" /> Todos
        </button>
      </div>

      {loading && <div className="flex justify-center py-12"><Spinner /></div>}

      {/* Para ti tab */}
      {tab === "para_ti" && !loading && (
        <>
          {matched?.contracts?.length > 0 ? (
            <>
              <p className="text-sm text-gray-500">{matched.contracts.length} contratos recomendados según tu perfil</p>
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
            <EmptyState icon={FileText} title="Sin resultados" description="Intenta con otras palabras clave." />
          ) : (
            <div className="space-y-3">
              {results.contracts.map((c) => (
                <ContractCard key={c.id} c={c} />
              ))}
            </div>
          )}

          {results.total > 20 && (
            <div className="flex justify-center gap-2">
              <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => searchAll(page - 1)}>Anterior</Button>
              <span className="text-sm text-gray-500 py-1.5">Página {page} de {results.pages}</span>
              <Button variant="secondary" size="sm" disabled={results.contracts?.length < 20} onClick={() => searchAll(page + 1)}>Siguiente</Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function ContractCard({ c, showScore }) {
  const descGate = useGate("full_description");
  const scoreGate = useGate("match_scores");

  return (
    <Link to={`/contracts/${c.id}`}>
      <Card className="hover:shadow-md transition cursor-pointer">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-gray-900 truncate">{c.title}</h3>
              {showScore && c.match_score >= 60 && (
                scoreGate.allowed ? (
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold flex-shrink-0 ${
                    c.match_score >= 90 ? "bg-green-100 text-green-800" :
                    c.match_score >= 80 ? "bg-blue-100 text-blue-800" :
                    c.match_score >= 70 ? "bg-yellow-100 text-yellow-800" :
                    "bg-gray-100 text-gray-700"
                  }`}>
                    {c.match_score}% match
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-gray-100 text-gray-400 flex-shrink-0">
                    <Lock className="h-3 w-3" /> ??%
                  </span>
                )
              )}
            </div>
            <p className="text-xs text-gray-500 mt-1">{c.entity} · {c.source}</p>
            {c.description && (
              <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                {descGate.allowed ? c.description : truncate(c.description, 100)}
              </p>
            )}
            {c.description && !descGate.allowed && c.description.length > 100 && (
              <p className="text-xs text-brand-600 mt-1 font-medium">Activa Alertas para ver la descripción completa</p>
            )}
          </div>
          <div className="text-right flex-shrink-0 space-y-1">
            {c.amount && <p className="text-sm font-bold">{money(c.amount)}</p>}
            <Badge color={c.source?.includes("SECOP") ? "blue" : "purple"}>{c.source}</Badge>
            {c.deadline && <p className="text-xs text-gray-500">{relative(c.deadline)}</p>}
          </div>
        </div>
      </Card>
    </Link>
  );
}
