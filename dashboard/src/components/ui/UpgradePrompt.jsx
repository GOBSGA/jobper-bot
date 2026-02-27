import { Link } from "react-router-dom";
import { Lock, Sparkle } from "@phosphor-icons/react";
import { PLAN_INFO } from "../../hooks/useGate";

export default function UpgradePrompt({ feature, requiredPlan, children, message }) {
  const normalizedPlan = {
    alertas: "cazador", starter: "cazador",
    business: "competidor", enterprise: "dominador",
  }[requiredPlan] || requiredPlan || "cazador";

  const planInfo = PLAN_INFO[normalizedPlan] || PLAN_INFO.cazador;

  return (
    <div className="relative">
      <div className="opacity-30 pointer-events-none select-none blur-[2px]">
        {children}
      </div>
      <div className="absolute inset-0 flex items-center justify-center rounded-2xl bg-white/80 backdrop-blur-[3px]">
        <div className="text-center px-6">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-2xl bg-surface-hover mb-3">
            <Lock size={18} className="text-ink-400" weight="light" />
          </div>
          <p className="text-sm font-semibold text-ink-900 mb-1">
            {message || `Disponible en ${planInfo.emoji} ${planInfo.displayName}`}
          </p>
          <p className="text-xs text-ink-400 mb-3">{planInfo.priceText}</p>
          <Link
            to={`/payments?plan=${normalizedPlan}${feature ? `&feature=${feature}` : ""}`}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-medium bg-brand-500 text-white hover:bg-brand-600 transition-colors"
          >
            <Sparkle size={13} weight="fill" />
            Actualizar plan
          </Link>
        </div>
      </div>
    </div>
  );
}
