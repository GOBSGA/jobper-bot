import { useParams, useNavigate, Link } from "react-router-dom";
import { useApi, useMutation } from "../../hooks/useApi";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { useGate } from "../../hooks/useGate";
import { money, date, truncate } from "../../lib/format";
import { Heart, GitBranch, ExternalLink, ArrowLeft, Lock, Zap } from "lucide-react";
import { useToast } from "../../components/ui/Toast";

export default function ContractDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const { data: c, loading, refetch } = useApi(`/contracts/${id}`);
  const { mutate: toggleFav, loading: favLoading } = useMutation("post", `/contracts/favorite`);
  const { mutate: addPipeline } = useMutation("post", "/pipeline");
  const descGate = useGate("full_description");

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  if (!c) return null;

  const handleFav = async () => {
    try {
      await toggleFav({ contract_id: c.id });
      refetch();
    } catch (err) {
      if (err.upgrade) {
        toast.error("Límite de favoritos alcanzado. Actualiza tu plan.");
        navigate("/payments");
      } else {
        toast.error(err.error || "Error al guardar favorito");
      }
    }
  };

  const handlePipeline = async () => {
    await addPipeline({ contract_id: c.id, stage: "lead", value: c.amount });
    navigate("/pipeline");
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Volver
      </button>

      <Card>
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <h1 className="text-xl font-bold text-gray-900">{c.title}</h1>
            <div className="flex gap-2 flex-shrink-0">
              <Button variant="ghost" size="sm" onClick={handleFav} disabled={favLoading}>
                <Heart className={`h-4 w-4 ${c.is_favorited ? "fill-red-500 text-red-500" : ""}`} />
              </Button>
              <Button variant="secondary" size="sm" onClick={handlePipeline}>
                <GitBranch className="h-4 w-4" /> Pipeline
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge color="blue">{c.source}</Badge>
            {c.entity && <Badge>{c.entity}</Badge>}
            {c.city && <Badge color="purple">{c.city}</Badge>}
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-gray-500">Presupuesto:</span> <strong>{money(c.amount)}</strong></div>
            <div><span className="text-gray-500">Fecha límite:</span> <strong>{date(c.deadline)}</strong></div>
            <div><span className="text-gray-500">Publicado:</span> {date(c.publication_date || c.created_at)}</div>
            {c.external_id && <div><span className="text-gray-500">ID:</span> {c.external_id}</div>}
          </div>

          {c.url && (
            <a href={c.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-600 hover:underline">
              Ver en fuente original <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      </Card>

      {c.description && (
        <Card>
          <h2 className="font-semibold text-gray-900 mb-2">Descripción</h2>
          {descGate.allowed ? (
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{c.description}</p>
          ) : (
            <div>
              <p className="text-sm text-gray-700">{truncate(c.description, 150)}</p>
              <div className="mt-4 bg-gradient-to-b from-transparent to-gray-50 border border-gray-200 rounded-xl p-4 text-center">
                <Lock className="h-5 w-5 text-gray-400 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-700">Descripción completa disponible en plan Alertas</p>
                <Link to="/payments" className="inline-flex items-center gap-1 mt-2 px-4 py-1.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition">
                  <Zap className="h-3.5 w-3.5" /> Ver planes
                </Link>
              </div>
            </div>
          )}
        </Card>
      )}

      {c.analysis && (
        <Card>
          <h2 className="font-semibold text-gray-900 mb-2">Análisis inteligente</h2>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{c.analysis}</p>
        </Card>
      )}
    </div>
  );
}
