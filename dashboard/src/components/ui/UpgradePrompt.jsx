import { Link } from "react-router-dom";
import { Lock, Sparkles } from "lucide-react";
import { PLAN_INFO } from "../../hooks/useGate";

/**
 * UpgradePrompt — Overlay de bloqueo con CTA de upgrade
 * Versión actualizada para los 4 nuevos planes
 */
export default function UpgradePrompt({ feature, requiredPlan, children, message }) {
  // Normalizar plan names (compatibilidad con código viejo)
  const normalizedPlan = {
    alertas: "cazador",
    starter: "cazador",
    business: "competidor",
    enterprise: "dominador",
  }[requiredPlan] || requiredPlan || "cazador";

  const planInfo = PLAN_INFO[normalizedPlan] || PLAN_INFO.cazador;

  return (
    <div className="relative">
      {/* Contenido con opacity reducida y blur */}
      <div className="opacity-40 pointer-events-none select-none blur-[1px]">
        {children}
      </div>

      {/* Overlay de upgrade */}
      <div className="absolute inset-0 flex items-center justify-center bg-white/60 backdrop-blur-[2px] rounded-lg">
        <div className="text-center px-4 py-3">
          <div
            className={`
              inline-flex items-center justify-center w-10 h-10 rounded-full mb-2
              ${normalizedPlan === "dominador" ? "bg-amber-100" : ""}
              ${normalizedPlan === "competidor" ? "bg-purple-100" : ""}
              ${normalizedPlan === "cazador" ? "bg-blue-100" : "bg-gray-100"}
            `}
          >
            <Lock
              className={`
                h-5 w-5
                ${normalizedPlan === "dominador" ? "text-amber-600" : ""}
                ${normalizedPlan === "competidor" ? "text-purple-600" : ""}
                ${normalizedPlan === "cazador" ? "text-blue-600" : "text-gray-400"}
              `}
            />
          </div>

          <p className="text-sm font-semibold text-gray-700 mb-1">
            {message || `Disponible en ${planInfo.emoji} ${planInfo.displayName}`}
          </p>
          <p className="text-xs text-gray-500 mb-2">{planInfo.priceText}</p>

          <Link
            to={`/payments?plan=${normalizedPlan}${feature ? `&feature=${feature}` : ""}`}
            className={`
              inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium
              text-white transition-all duration-200 hover:scale-105
              ${normalizedPlan === "dominador" ? "bg-amber-500 hover:bg-amber-600" : ""}
              ${normalizedPlan === "competidor" ? "bg-purple-500 hover:bg-purple-600" : ""}
              ${normalizedPlan === "cazador" ? "bg-blue-500 hover:bg-blue-600" : "bg-brand-600 hover:bg-brand-700"}
            `}
          >
            <Sparkles className="h-3.5 w-3.5" />
            Actualizar plan
          </Link>
        </div>
      </div>
    </div>
  );
}
