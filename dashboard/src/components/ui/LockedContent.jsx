import { Link } from "react-router-dom";
import { Lock, Sparkles, Eye, TrendingUp, Zap } from "lucide-react";
import { PLAN_INFO } from "../../hooks/useGate";

/**
 * LockedContent — Componente de FOMO visual para features bloqueadas
 *
 * Modos:
 * - blur: Muestra contenido con blur y overlay de upgrade
 * - inline: Reemplaza texto con placeholder bloqueado (ej: "??%")
 * - banner: Banner horizontal con CTA de upgrade
 * - card: Card completa de upgrade con beneficios
 */

// =============================================================================
// BLUR MODE — Contenido con blur y overlay
// =============================================================================
export function LockedBlur({
  children,
  feature,
  requiredPlan,
  message,
  showButton = true,
  blurAmount = "sm",
}) {
  const planInfo = PLAN_INFO[requiredPlan] || PLAN_INFO.cazador;

  return (
    <div className="relative group">
      {/* Contenido con blur */}
      <div
        className={`
          opacity-50 pointer-events-none select-none
          filter blur-${blurAmount}
          transition-all duration-300
          group-hover:blur-md
        `}
      >
        {children}
      </div>

      {/* Overlay de upgrade */}
      <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-b from-white/40 via-white/70 to-white/90 rounded-lg">
        <div className="text-center px-6 py-4">
          <div
            className={`
              inline-flex items-center justify-center w-12 h-12 rounded-full mb-3
              ${requiredPlan === "dominador" ? "bg-amber-100" : ""}
              ${requiredPlan === "competidor" ? "bg-purple-100" : ""}
              ${requiredPlan === "cazador" ? "bg-blue-100" : ""}
            `}
          >
            <Lock
              className={`
                h-6 w-6
                ${requiredPlan === "dominador" ? "text-amber-600" : ""}
                ${requiredPlan === "competidor" ? "text-purple-600" : ""}
                ${requiredPlan === "cazador" ? "text-blue-600" : ""}
              `}
            />
          </div>

          <p className="text-sm font-semibold text-gray-800 mb-1">
            {message || `Disponible en ${planInfo.emoji} ${planInfo.displayName}`}
          </p>
          <p className="text-xs text-gray-500 mb-3">{planInfo.priceText}</p>

          {showButton && (
            <Link
              to={`/payments?plan=${requiredPlan}&feature=${feature}`}
              className={`
                inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                text-white transition-all duration-200 hover:scale-105 shadow-lg
                ${requiredPlan === "dominador" ? "bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700" : ""}
                ${requiredPlan === "competidor" ? "bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700" : ""}
                ${requiredPlan === "cazador" ? "bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700" : ""}
              `}
            >
              <Sparkles className="h-4 w-4" />
              Desbloquear
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// INLINE LOCKED — Texto bloqueado inline (ej: "??%" o "$🔒🔒🔒")
// =============================================================================
export function LockedInline({
  type = "score", // score, amount, text
  requiredPlan = "cazador",
  className = "",
  onClick,
}) {
  const planInfo = PLAN_INFO[requiredPlan] || PLAN_INFO.cazador;

  const content = {
    score: (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded text-gray-400 font-mono">
        <Lock className="h-3 w-3" />
        ??%
      </span>
    ),
    amount: (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded text-gray-400">
        <Lock className="h-3 w-3" />
        $•••••
      </span>
    ),
    text: (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded text-gray-400 text-sm">
        <Lock className="h-3 w-3" />
        Bloqueado
      </span>
    ),
  };

  const Wrapper = onClick ? "button" : "span";

  return (
    <Wrapper
      onClick={onClick}
      className={`
        cursor-pointer hover:bg-gray-200 transition-colors rounded
        ${className}
      `}
      title={`Desbloquea con ${planInfo.displayName}`}
    >
      {content[type] || content.text}
    </Wrapper>
  );
}

// =============================================================================
// FOMO BANNER — Banner horizontal con estadísticas y CTA
// =============================================================================
export function FomoBanner({
  count,
  feature,
  requiredPlan = "cazador",
  message,
  onDismiss,
}) {
  const planInfo = PLAN_INFO[requiredPlan] || PLAN_INFO.cazador;

  const defaultMessages = {
    match_scores: `${count} contratos coinciden con tu perfil — ve tu % de compatibilidad`,
    private_contracts: `${count} contratos privados disponibles solo en ${planInfo.displayName}`,
    alerts: `Hay ${count} contratos nuevos hoy — activa alertas para no perdértelos`,
    full_description: `Estás viendo solo el resumen — desbloquea descripciones completas`,
  };

  return (
    <div
      className={`
        relative overflow-hidden rounded-lg p-4 mb-4
        ${requiredPlan === "dominador" ? "bg-gradient-to-r from-amber-50 to-amber-100 border border-amber-200" : ""}
        ${requiredPlan === "competidor" ? "bg-gradient-to-r from-purple-50 to-purple-100 border border-purple-200" : ""}
        ${requiredPlan === "cazador" ? "bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200" : ""}
      `}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={`
              flex-shrink-0 p-2 rounded-full
              ${requiredPlan === "dominador" ? "bg-amber-200" : ""}
              ${requiredPlan === "competidor" ? "bg-purple-200" : ""}
              ${requiredPlan === "cazador" ? "bg-blue-200" : ""}
            `}
          >
            {feature === "match_scores" && <TrendingUp className="h-5 w-5 text-current" />}
            {feature === "private_contracts" && <Eye className="h-5 w-5 text-current" />}
            {feature === "alerts" && <Zap className="h-5 w-5 text-current" />}
            {!["match_scores", "private_contracts", "alerts"].includes(feature) && (
              <Sparkles className="h-5 w-5 text-current" />
            )}
          </div>

          <div>
            <p className="font-semibold text-gray-900">
              {message || defaultMessages[feature] || `Desbloquea ${feature}`}
            </p>
            <p className="text-sm text-gray-600">
              {planInfo.emoji} {planInfo.displayName} — {planInfo.priceText}
            </p>
          </div>
        </div>

        <Link
          to={`/payments?plan=${requiredPlan}&feature=${feature}`}
          className={`
            flex-shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
            text-white transition-all duration-200 hover:scale-105
            ${requiredPlan === "dominador" ? "bg-amber-500 hover:bg-amber-600" : ""}
            ${requiredPlan === "competidor" ? "bg-purple-500 hover:bg-purple-600" : ""}
            ${requiredPlan === "cazador" ? "bg-blue-500 hover:bg-blue-600" : ""}
          `}
        >
          Activar
        </Link>
      </div>

      {onDismiss && (
        <button
          onClick={onDismiss}
          className="absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600"
        >
          ×
        </button>
      )}
    </div>
  );
}

// =============================================================================
// UPGRADE CARD — Card completa con beneficios
// =============================================================================
export function UpgradeCard({ requiredPlan = "cazador", benefits = [], compact = false }) {
  const planInfo = PLAN_INFO[requiredPlan] || PLAN_INFO.cazador;

  const defaultBenefits = {
    cazador: [
      "Descripciones completas de contratos",
      "Match score de compatibilidad",
      "Montos de contratos visibles",
      "Alertas por email",
      "Exportar a Excel",
    ],
    competidor: [
      "Todo de Cazador +",
      "Contratos privados exclusivos",
      "Análisis de IA por contrato",
      "Pipeline de seguimiento",
      "Alertas instantáneas push",
    ],
    dominador: [
      "Todo de Competidor +",
      "Inteligencia competitiva",
      "5 usuarios incluidos",
      "Auto-generación de propuestas",
      "Soporte prioritario WhatsApp",
    ],
  };

  const featureList = benefits.length > 0 ? benefits : defaultBenefits[requiredPlan] || [];

  if (compact) {
    return (
      <Link
        to={`/payments?plan=${requiredPlan}`}
        className={`
          block p-4 rounded-lg border-2 transition-all duration-200 hover:scale-[1.02]
          ${requiredPlan === "dominador" ? "border-amber-300 bg-amber-50 hover:border-amber-400" : ""}
          ${requiredPlan === "competidor" ? "border-purple-300 bg-purple-50 hover:border-purple-400" : ""}
          ${requiredPlan === "cazador" ? "border-blue-300 bg-blue-50 hover:border-blue-400" : ""}
        `}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{planInfo.emoji}</span>
            <div>
              <p className="font-semibold">{planInfo.displayName}</p>
              <p className="text-sm text-gray-600">{planInfo.priceText}</p>
            </div>
          </div>
          <Sparkles className="h-5 w-5 text-gray-400" />
        </div>
      </Link>
    );
  }

  return (
    <div
      className={`
        rounded-xl border-2 overflow-hidden
        ${requiredPlan === "dominador" ? "border-amber-300" : ""}
        ${requiredPlan === "competidor" ? "border-purple-300" : ""}
        ${requiredPlan === "cazador" ? "border-blue-300" : ""}
      `}
    >
      {/* Header */}
      <div
        className={`
          px-6 py-4
          ${requiredPlan === "dominador" ? "bg-gradient-to-r from-amber-500 to-amber-600" : ""}
          ${requiredPlan === "competidor" ? "bg-gradient-to-r from-purple-500 to-purple-600" : ""}
          ${requiredPlan === "cazador" ? "bg-gradient-to-r from-blue-500 to-blue-600" : ""}
        `}
      >
        <div className="flex items-center gap-3 text-white">
          <span className="text-3xl">{planInfo.emoji}</span>
          <div>
            <h3 className="text-xl font-bold">{planInfo.displayName}</h3>
            <p className="text-white/80">{planInfo.priceText}</p>
          </div>
        </div>
      </div>

      {/* Benefits */}
      <div className="p-6 bg-white">
        <ul className="space-y-3 mb-6">
          {featureList.map((benefit, i) => (
            <li key={i} className="flex items-start gap-2">
              <Sparkles className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
              <span className="text-gray-700">{benefit}</span>
            </li>
          ))}
        </ul>

        <Link
          to={`/payments?plan=${requiredPlan}`}
          className={`
            block w-full text-center py-3 rounded-lg font-semibold text-white
            transition-all duration-200 hover:scale-[1.02]
            ${requiredPlan === "dominador" ? "bg-amber-500 hover:bg-amber-600" : ""}
            ${requiredPlan === "competidor" ? "bg-purple-500 hover:bg-purple-600" : ""}
            ${requiredPlan === "cazador" ? "bg-blue-500 hover:bg-blue-600" : ""}
          `}
        >
          Activar {planInfo.displayName}
        </Link>
      </div>
    </div>
  );
}

// =============================================================================
// DEFAULT EXPORT
// =============================================================================
export default LockedBlur;
