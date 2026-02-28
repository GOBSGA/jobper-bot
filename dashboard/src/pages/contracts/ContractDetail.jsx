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
import {
  Heart,
  GitBranch,
  ArrowLeft,
  Lock,
  Lightning,
  Brain,
  Warning,
  CheckCircle,
  ArrowSquareOut,
  Sparkle,
} from "@phosphor-icons/react";
import { useToast } from "../../components/ui/Toast";

function stripHtml(html) {
  if (!html) return "";
  return html.replace(/<[^>]*>/g, " ").replace(/\*\*/g, "").replace(/\s+/g, " ").trim();
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
  const pipelineGate = useGate("pipeline");

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

  if (loading)
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    );
  if (!c)
    return (
      <div className="max-w-3xl mx-auto py-12 text-center space-y-4">
        <p className="text-ink-400">No se pudo cargar el contrato.</p>
        <Button onClick={refetch} variant="secondary">
          Reintentar
        </Button>
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
    <div className="max-w-3xl mx-auto space-y-4 pb-8">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 text-sm text-ink-400 hover:text-ink-900 transition-colors"
      >
        <ArrowLeft size={16} weight="bold" /> Volver
      </button>

      {/* Main info card */}
      <Card className="p-5 sm:p-6">
        <div className="space-y-4">
          {/* Title + Actions */}
          <div className="flex items-start justify-between gap-4">
            <h1 className="text-lg sm:text-xl font-bold text-ink-900 leading-snug">{c.title}</h1>
            <div className="flex gap-2 flex-shrink-0">
              <Button variant="ghost" size="sm" onClick={handleFav} disabled={favLoading}>
                <Heart
                  size={16}
                  weight={c.is_favorited ? "fill" : "regular"}
                  className={c.is_favorited ? "text-red-500" : "text-ink-400"}
                />
              </Button>
              {pipelineGate.allowed ? (
                <Button variant="secondary" size="sm" onClick={handlePipeline}>
                  <GitBranch size={15} /> Pipeline
                </Button>
              ) : (
                <Link to={pipelineGate.upgradeUrl}>
                  <Button
                    variant="ghost"
                    size="sm"
                    title={pipelineGate.fomoMessage || "Requiere plan Competidor"}
                  >
                    <Lock size={15} className="text-ink-400" />
                  </Button>
                </Link>
              )}
            </div>
          </div>

          {/* Badges */}
          <div className="flex flex-wrap gap-2">
            <Badge color="blue">{c.source}</Badge>
            {c.entity && <Badge>{c.entity}</Badge>}
            {c.city && <Badge color="purple">{c.city}</Badge>}
          </div>

          {/* Meta grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div className="flex items-baseline gap-1.5">
              <span className="text-ink-400 flex-shrink-0">Presupuesto:</span>
              <strong className="text-ink-900 text-base">{money(c.amount)}</strong>
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-ink-400 flex-shrink-0">Fecha límite:</span>
              <strong className="text-ink-900">{date(c.deadline)}</strong>
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-ink-400 flex-shrink-0">Publicado:</span>
              <span className="text-ink-600">{date(c.publication_date || c.created_at)}</span>
            </div>
            {c.external_id && (
              <div className="flex items-baseline gap-1.5">
                <span className="text-ink-400 flex-shrink-0">ID:</span>
                <span className="text-ink-600 font-mono text-xs">{c.external_id}</span>
              </div>
            )}
          </div>

          {/* External link */}
          {c.url && (
            <a
              href={c.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-brand-600 hover:underline"
            >
              Ver en fuente original <ArrowSquareOut size={13} />
            </a>
          )}
        </div>
      </Card>

      {/* Description */}
      {c.description && (
        <Card className="p-5 sm:p-6">
          <h2 className="font-semibold text-ink-900 mb-3">Descripción</h2>
          {descGate.allowed ? (
            /<[a-z][\s\S]*>/i.test(c.description) ? (
              <div
                className="text-sm text-ink-600 leading-relaxed [&_p]:mb-2 [&_strong]:font-semibold [&_table]:w-full [&_table]:border-collapse [&_td]:border [&_td]:border-surface-border [&_td]:p-2 [&_th]:border [&_th]:border-surface-border [&_th]:p-2 [&_th]:bg-surface-hover [&_ul]:list-disc [&_ul]:pl-4 [&_ol]:list-decimal [&_ol]:pl-4"
                dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(c.description) }}
              />
            ) : (
              <p className="text-sm text-ink-600 whitespace-pre-wrap leading-relaxed">
                {c.description.replace(/\*\*/g, "")}
              </p>
            )
          ) : (
            <div>
              <p className="text-sm text-ink-600 leading-relaxed">
                {truncate(stripHtml(c.description), 200)}
              </p>
              <div className="mt-4 border border-surface-border rounded-xl p-5 text-center bg-surface-hover">
                <Lock size={20} className="text-ink-400 mx-auto mb-2" />
                <p className="text-sm font-medium text-ink-900">
                  Descripción completa disponible en plan Cazador
                </p>
                <Link
                  to="/payments"
                  className="inline-flex items-center gap-1.5 mt-3 px-4 py-1.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition"
                >
                  <Lightning size={13} /> Ver planes
                </Link>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* AI Analysis */}
      <Card className="p-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-ink-900 flex items-center gap-2">
            <Sparkle size={16} className="text-purple-500" weight="duotone" /> Análisis con IA
          </h2>
          {analysisGate.allowed && !analysis && (
            <Button size="sm" onClick={handleAnalyze} disabled={analyzingAI}>
              {analyzingAI ? (
                <>
                  <Spinner className="h-3.5 w-3.5 mr-1" /> Analizando...
                </>
              ) : (
                <>
                  <Lightning size={13} /> Analizar
                </>
              )}
            </Button>
          )}
          {analysisGate.allowed && analysis && (
            <button
              onClick={handleAnalyze}
              disabled={analyzingAI}
              className="text-xs text-ink-400 hover:text-ink-600 transition"
            >
              {analyzingAI ? "Actualizando..." : "Actualizar"}
            </button>
          )}
        </div>

        {!analysisGate.allowed ? (
          <div className="text-center py-4">
            <Lock size={20} className="text-ink-400 mx-auto mb-2" />
            <p className="text-sm text-ink-400">
              {analysisGate.fomoMessage || "Análisis IA disponible en plan Competidor"}
            </p>
            <Link
              to={analysisGate.upgradeUrl || "/payments"}
              className="inline-flex items-center gap-1 mt-2 text-xs text-brand-600 hover:underline"
            >
              <Lightning size={11} /> Ver planes
            </Link>
          </div>
        ) : analyzingAI && !analysis ? (
          <div className="flex items-center justify-center py-8 gap-3 text-ink-400">
            <Spinner className="h-5 w-5" />
            <span className="text-sm">Analizando el contrato con IA...</span>
          </div>
        ) : analysis ? (
          <AnalysisCard analysis={analysis} />
        ) : (
          <p className="text-sm text-ink-400 text-center py-4">
            Haz clic en "Analizar" para obtener un análisis detallado de este contrato.
          </p>
        )}
      </Card>
    </div>
  );
}

function AnalysisCard({ analysis }) {
  const scoreColor = (s) =>
    s >= 70 ? "text-accent-700" : s >= 40 ? "text-amber-600" : "text-red-500";
  const scoreBg = (s) =>
    s >= 70 ? "bg-accent-50" : s >= 40 ? "bg-amber-50" : "bg-red-50";
  const complexityLabel = {
    simple: "Simple",
    moderate: "Moderado",
    complex: "Complejo",
    highly_complex: "Muy complejo",
  };
  const competitionLabel = {
    low: "Baja",
    moderate: "Moderada",
    high: "Alta",
    very_high: "Muy alta",
  };

  return (
    <div className="space-y-4">
      {/* Scores */}
      <div className="grid grid-cols-2 gap-3">
        {analysis.opportunity_score != null && (
          <div className={`${scoreBg(analysis.opportunity_score)} rounded-xl p-3 text-center`}>
            <p className={`text-2xl font-bold ${scoreColor(analysis.opportunity_score)}`}>
              {analysis.opportunity_score}%
            </p>
            <p className="text-xs text-ink-400 mt-1">Oportunidad</p>
          </div>
        )}
        {analysis.fit_score != null && (
          <div className={`${scoreBg(analysis.fit_score)} rounded-xl p-3 text-center`}>
            <p className={`text-2xl font-bold ${scoreColor(analysis.fit_score)}`}>
              {analysis.fit_score}%
            </p>
            <p className="text-xs text-ink-400 mt-1">Encaje con tu perfil</p>
          </div>
        )}
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-2 text-xs">
        {analysis.contract_type && (
          <span className="px-2.5 py-1 bg-brand-50 text-brand-600 rounded-full font-medium">
            {analysis.contract_type}
          </span>
        )}
        {analysis.complexity && (
          <span className="px-2.5 py-1 bg-purple-50 text-purple-700 rounded-full font-medium">
            {complexityLabel[analysis.complexity] || analysis.complexity}
          </span>
        )}
        {analysis.competition_level && (
          <span className="px-2.5 py-1 bg-amber-50 text-amber-700 rounded-full font-medium">
            Competencia: {competitionLabel[analysis.competition_level] || analysis.competition_level}
          </span>
        )}
        {analysis.estimated_duration_days && (
          <span className="px-2.5 py-1 bg-surface-hover text-ink-600 rounded-full font-medium">
            ~{analysis.estimated_duration_days} días
          </span>
        )}
        {analysis.requires_consortium && (
          <span className="px-2.5 py-1 bg-amber-50 text-amber-700 rounded-full font-medium">
            Requiere consorcio
          </span>
        )}
        {analysis.requires_local_presence && (
          <span className="px-2.5 py-1 bg-red-50 text-red-700 rounded-full font-medium">
            Presencia local requerida
          </span>
        )}
      </div>

      {/* Requirements */}
      {analysis.requirements?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-ink-400 uppercase tracking-wide mb-2">
            Requisitos clave
          </p>
          <ul className="space-y-1.5">
            {analysis.requirements.slice(0, 5).map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-ink-700">
                <CheckCircle
                  size={14}
                  className="text-accent-500 flex-shrink-0 mt-0.5"
                  weight="fill"
                />
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {analysis.warnings?.length > 0 && (
        <div className="bg-amber-50 border border-amber-100 rounded-xl p-3">
          <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-2">
            Alertas
          </p>
          <ul className="space-y-1.5">
            {analysis.warnings.map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-amber-800">
                <Warning size={14} className="flex-shrink-0 mt-0.5" weight="fill" />
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {analysis.recommendations?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-ink-400 uppercase tracking-wide mb-2">
            Recomendaciones
          </p>
          <ul className="space-y-1.5">
            {analysis.recommendations.map((r, i) => (
              <li key={i} className="text-sm text-ink-700 pl-3 border-l-2 border-brand-300">
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
