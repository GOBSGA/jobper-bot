import { useAuth } from "../context/AuthContext";
import { PLAN_ORDER, normalizePlan as normalize } from "../lib/planConfig";

// =============================================================================
// FEATURE GATES — Qué plan necesita cada feature
// =============================================================================
const FEATURE_GATES = {
  // === CAZADOR ($30K) ===
  full_description: "cazador",
  match_scores: "cazador",
  show_amount: "cazador",
  alerts_email: "cazador",
  favorites_unlimited: "cazador",
  email_digest: "cazador",
  advanced_filters: "cazador",
  export: "cazador",
  saved_searches: "cazador",
  // Legacy aliases
  alerts: "cazador",
  favorites: "cazador",
  match: "cazador",

  // === COMPETIDOR ($150K) ===
  private_contracts: "competidor",
  ai_analysis: "competidor",
  pipeline: "competidor",
  alerts_push: "competidor",
  instant_alerts: "competidor",
  documents: "competidor",
  webinars: "competidor",
  // Legacy aliases
  push: "competidor",
  marketplace: "competidor",
  reports: "competidor",

  // === DOMINADOR ($600K) ===
  competitive_intelligence: "dominador",
  team: "dominador",
  api_access: "dominador",
  auto_proposals: "dominador",
  consortium_network: "dominador",
  priority_support: "dominador",
  monthly_consultation: "dominador",
  custom_reports: "dominador",
  whitelabel: "dominador",
  // Legacy alias
  enterprise: "dominador",
};

// =============================================================================
// FOMO MESSAGES — Mensajes que crean urgencia
// =============================================================================
const FOMO_MESSAGES = {
  full_description: "Desbloquea la descripción completa",
  match_scores: "Ve tu % de compatibilidad con este contrato",
  show_amount: "Descubre cuánto vale este contrato",
  private_contracts: "Accede a contratos privados exclusivos",
  ai_analysis: "Analiza con IA tu probabilidad de ganar",
  competitive_intelligence: "Descubre quién gana en tu sector",
  alerts_email: "Recibe alertas de nuevos contratos",
  saved_searches: "Guarda búsquedas y recibe alertas automáticas",
  instant_alerts: "Sé el primero en enterarte",
  pipeline: "Gestiona tu pipeline de contratos",
  team: "Añade a tu equipo",
  export: "Exporta contratos a Excel",
  documents: "Descarga pliegos y documentos",
};

// =============================================================================
// PLAN INFO — Información para mostrar en UI
// =============================================================================
export const PLAN_INFO = {
  free: {
    name: "Gratis",
    displayName: "Observador",
    price: 0,
    priceText: "Gratis",
    color: "gray",
    emoji: "👀",
  },
  cazador: {
    name: "Cazador",
    displayName: "Cazador",
    price: 29900,
    priceText: "$29.900/mes",
    color: "blue",
    emoji: "🎯",
  },
  competidor: {
    name: "Competidor",
    displayName: "Competidor",
    price: 149900,
    priceText: "$149.900/mes",
    color: "purple",
    emoji: "⚔️",
  },
  dominador: {
    name: "Dominador",
    displayName: "Dominador",
    price: 599900,
    priceText: "$599.900/mes",
    color: "gold",
    emoji: "👑",
  },
};

// =============================================================================
// useGate HOOK — Verifica si el usuario tiene acceso a una feature
// =============================================================================
export function useGate(feature) {
  const { user } = useAuth();
  const rawPlan = user?.plan || "free";
  const userPlan = normalize(rawPlan);
  const requiredPlan = FEATURE_GATES[feature];

  // Si no está en gates, permitir
  if (!requiredPlan) {
    return {
      allowed: true,
      requiredPlan: null,
      currentPlan: userPlan,
      fomoMessage: null,
      upgradeUrl: null,
    };
  }

  const userLevel = PLAN_ORDER[userPlan] ?? 0;
  const requiredLevel = PLAN_ORDER[requiredPlan] ?? 0;
  const allowed = userLevel >= requiredLevel;

  return {
    allowed,
    requiredPlan: normalize(requiredPlan),
    currentPlan: userPlan,
    fomoMessage: allowed ? null : FOMO_MESSAGES[feature] || `Requiere plan ${requiredPlan}`,
    upgradeUrl: allowed ? null : `/payments?plan=${requiredPlan}&feature=${feature}`,
    planInfo: PLAN_INFO[normalize(requiredPlan)],
  };
}

// =============================================================================
// usePlanLimits HOOK — Obtiene los límites del plan actual
// =============================================================================
export function usePlanLimits() {
  const { user } = useAuth();
  const rawPlan = user?.plan || "free";
  const userPlan = normalize(rawPlan);

  const limits = {
    free: {
      searches_per_day: 10,
      favorites_max: 10,
      alerts_per_week: 3,  // FIX: Synced with backend - 3 basic alerts/week
      export_per_month: 0,
      show_full_description: false,
      show_match_score: false,
      show_amount: false,
    },
    cazador: {
      searches_per_day: null,
      favorites_max: 100,
      alerts_per_week: 50,
      export_per_month: 50,
      show_full_description: true,
      show_match_score: true,
      show_amount: true,
    },
    competidor: {
      searches_per_day: null,
      favorites_max: null,
      alerts_per_week: null,
      export_per_month: 500,
      show_full_description: true,
      show_match_score: true,
      show_amount: true,
    },
    dominador: {
      searches_per_day: null,
      favorites_max: null,
      alerts_per_week: null,
      export_per_month: null,
      show_full_description: true,
      show_match_score: true,
      show_amount: true,
    },
  };

  return {
    plan: userPlan,
    planInfo: PLAN_INFO[userPlan],
    limits: limits[userPlan] || limits.free,
    isFreeTier: userPlan === "free",
    isPaid: userPlan !== "free",
  };
}

// =============================================================================
// useUpgradePrompt HOOK — Para mostrar prompts de upgrade contextuales
// =============================================================================
export function useUpgradePrompt() {
  const { user } = useAuth();
  const userPlan = normalize(user?.plan || "free");

  const getNextPlan = () => {
    if (userPlan === "free") return "cazador";
    if (userPlan === "cazador") return "competidor";
    if (userPlan === "competidor") return "dominador";
    return null;
  };

  const nextPlan = getNextPlan();

  return {
    currentPlan: userPlan,
    currentPlanInfo: PLAN_INFO[userPlan],
    nextPlan,
    nextPlanInfo: nextPlan ? PLAN_INFO[nextPlan] : null,
    canUpgrade: nextPlan !== null,
    upgradeUrl: nextPlan ? `/payments?plan=${nextPlan}` : null,
  };
}

export default useGate;
