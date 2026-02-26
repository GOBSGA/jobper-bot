import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import DOMPurify from "dompurify";
import { useApi, useMutation } from "../../hooks/useApi";
import { api } from "../../lib/api";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { useGate } from "../../hooks/useGate";
import { money, date, truncate } from "../../lib/format";
import { Heart, GitBranch, ExternalLink, ArrowLeft, Lock, Zap, Brain, AlertTriangle, CheckCircle } from "lucide-react";
import { useToast } from "../../components/ui/Toast";

function stripHtml(html) {
  return html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

export default function ContractDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const { data: c, loading, refetch } = useApi(`/contracts/${id}`);
  const { mutate: toggleFav, loading: favLoading } = useMutation("post", `/contracts/favorite`);
  const { mutate: addPipeline } = useMutation("post", "/pipeline");
  const descGate = useGate("full_description");
  const analysisGate = useGate("ai_analysis");

  const [analysis, setAnalysis] = useState(null);
  const [analyzingAI, setAnalyzingAI] = useState(false);

  useEffect(() => {
    if (c?.analysis) setAnalysis(c.analysis);
  }, [c]);

  const handleAnalyze = async () => {
    setAnalyzingAI(true);
    try {
      const data = await api.get(`/contracts/${id}/analysis`);
      setAnalysis(data);
    } catch (err) {
      toast.error(err.error || "Error generando análisis. Intenta de nuevo.");
    } finally {
      setAnalyzingAI(false);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  if (!c) return (
    <div className="max-w-3xl mx-auto py-12 text-center space-y-4">
      <p className="text-gray-600">No se pudo cargar el contrato.</p>
      <Button onClick={refetch} variant="secondary">Reintentar</Button>
    </div>
  );

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
    try {
      await addPipeline({ contract_id: c.id, stage: "lead", value: c.amount });
      navigate("/pipeline");
    } catch (err) {
      toast.error(err.error || "Error al agregar al pipeline");
    }
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
            /<[a-z][\s\S]*>/i.test(c.description) ? (
              <div
                className="text-sm text-gray-700 [&_p]:mb-2 [&_strong]:font-semibold [&_table]:w-full [&_table]:border-collapse [&_td]:border [&_td]:border-gray-200 [&_td]:p-1 [&_th]:border [&_th]:border-gray-200 [&_th]:p-1 [&_th]:bg-gray-50 [&_ul]:list-disc [&_ul]:pl-4 [&_ol]:list-decimal [&_ol]:pl-4"
                dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(c.description) }}
              />
            ) : (
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{c.description}</p>
            )
          ) : (
            <div>
              <p className="text-sm text-gray-700">{truncate(stripHtml(c.description), 150)}</p>
              <div className="mt-4 bg-gradient-to-b from-transparent to-gray-50 border border-gray-200 rounded-xl p-4 text-center">
                <Lock className="h-5 w-5 text-gray-400 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-700">Descripción completa disponible en plan Cazador</p>
                <Link to="/payments" className="inline-flex items-center gap-1 mt-2 px-4 py-1.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition">
                  <Zap className="h-3.5 w-3.5" /> Ver planes
                </Link>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* AI Analysis */}
      <Card>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <Brain className="h-4 w-4 text-purple-500" /> Análisis con IA
          </h2>
          {analysisGate.allowed && !analysis && (
            <Button size="sm" onClick={handleAnalyze} disabled={analyzingAI}>
              {analyzingAI ? <><Spinner className="h-3.5 w-3.5 mr-1" /> Analizando...</> : <><Zap className="h-3.5 w-3.5 mr-1" /> Analizar</>}
            </Button>
          )}
          {analysisGate.allowed && analysis && (
            <button onClick={handleAnalyze} disabled={analyzingAI} className="text-xs text-gray-400 hover:text-gray-600 transition">
              {analyzingAI ? "Actualizando..." : "Actualizar"}
            </button>
          )}
        </div>

        {!analysisGate.allowed ? (
          <div className="text-center py-4">
            <Lock className="h-5 w-5 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">Análisis IA disponible en plan Competidor</p>
            <Link to="/payments" className="inline-flex items-center gap-1 mt-2 text-xs text-brand-600 hover:underline">
              <Zap className="h-3 w-3" /> Ver planes
            </Link>
          </div>
        ) : analyzingAI && !analysis ? (
          <div className="flex items-center justify-center py-8 gap-3 text-gray-500">
            <Spinner className="h-5 w-5" />
            <span className="text-sm">Analizando el contrato con IA...</span>
          </div>
        ) : analysis ? (
          <AnalysisCard analysis={analysis} />
        ) : (
          <p className="text-sm text-gray-400 text-center py-4">
            Haz clic en "Analizar" para obtener un análisis detallado de este contrato.
          </p>
        )}
      </Card>
    </div>
  );
}

function AnalysisCard({ analysis }) {
  const scoreColor = (s) => s >= 70 ? "text-green-600" : s >= 40 ? "text-yellow-600" : "text-red-500";
  const complexityLabel = { simple: "Simple", moderate: "Moderado", complex: "Complejo", highly_complex: "Muy complejo" };
  const competitionLabel = { low: "Baja", moderate: "Moderada", high: "Alta", very_high: "Muy alta" };

  return (
    <div className="space-y-4">
      {/* Scores */}
      <div className="grid grid-cols-2 gap-3">
        {analysis.opportunity_score != null && (
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <p className={`text-2xl font-bold ${scoreColor(analysis.opportunity_score)}`}>{analysis.opportunity_score}%</p>
            <p className="text-xs text-gray-500 mt-1">Oportunidad</p>
          </div>
        )}
        {analysis.fit_score != null && (
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <p className={`text-2xl font-bold ${scoreColor(analysis.fit_score)}`}>{analysis.fit_score}%</p>
            <p className="text-xs text-gray-500 mt-1">Encaje con tu perfil</p>
          </div>
        )}
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-2 text-xs">
        {analysis.contract_type && <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-full">{analysis.contract_type}</span>}
        {analysis.complexity && <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded-full">{complexityLabel[analysis.complexity] || analysis.complexity}</span>}
        {analysis.competition_level && <span className="px-2 py-1 bg-orange-50 text-orange-700 rounded-full">Competencia: {competitionLabel[analysis.competition_level] || analysis.competition_level}</span>}
        {analysis.estimated_duration_days && <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full">~{analysis.estimated_duration_days} días</span>}
        {analysis.requires_consortium && <span className="px-2 py-1 bg-yellow-50 text-yellow-700 rounded-full">Requiere consorcio</span>}
        {analysis.requires_local_presence && <span className="px-2 py-1 bg-red-50 text-red-700 rounded-full">Presencia local requerida</span>}
      </div>

      {/* Requirements */}
      {analysis.requirements?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Requisitos clave</p>
          <ul className="space-y-1">
            {analysis.requirements.slice(0, 5).map((r, i) => (
              <li key={i} className="flex items-start gap-1.5 text-sm text-gray-700">
                <CheckCircle className="h-3.5 w-3.5 text-green-400 flex-shrink-0 mt-0.5" />{r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {analysis.warnings?.length > 0 && (
        <div className="bg-yellow-50 rounded-lg p-3">
          <p className="text-xs font-semibold text-yellow-700 uppercase tracking-wide mb-1.5">Alertas</p>
          <ul className="space-y-1">
            {analysis.warnings.map((w, i) => (
              <li key={i} className="flex items-start gap-1.5 text-sm text-yellow-800">
                <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />{w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {analysis.recommendations?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Recomendaciones</p>
          <ul className="space-y-1">
            {analysis.recommendations.map((r, i) => (
              <li key={i} className="text-sm text-gray-700 pl-3 border-l-2 border-brand-300">{r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
