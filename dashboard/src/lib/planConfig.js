/**
 * Centralized plan configuration and utilities
 * Single source of truth for plan hierarchy, colors, and benefits
 */

export const PLAN_ORDER = {
  free: 0,
  trial: 0,
  cazador: 1,
  competidor: 2,
  dominador: 3,
  // Legacy aliases
  alertas: 1,
  starter: 1,
  business: 2,
  enterprise: 3,
};

export const PLAN_ALIASES = {
  alertas: "cazador",
  starter: "cazador",
  business: "competidor",
  enterprise: "dominador",
  trial: "free",
};

export const normalizePlan = (plan) => PLAN_ALIASES[plan] || plan || "free";

export const PLAN_COLORS = {
  free: {
    bg: "bg-gray-100",
    text: "text-gray-600",
    border: "border-gray-300",
    light: "bg-gray-50",
    badge: "bg-gray-100 text-gray-600",
  },
  trial: {
    bg: "bg-blue-100",
    text: "text-blue-700",
    border: "border-blue-300",
    light: "bg-blue-50",
    badge: "bg-blue-100 text-blue-700",
  },
  cazador: {
    bg: "bg-green-100",
    text: "text-green-700",
    border: "border-green-300",
    light: "bg-green-50",
    badge: "bg-green-100 text-green-700",
  },
  competidor: {
    bg: "bg-brand-100",
    text: "text-brand-700",
    border: "border-brand-300",
    light: "bg-brand-50",
    badge: "bg-brand-100 text-brand-700",
  },
  dominador: {
    bg: "bg-purple-100",
    text: "text-purple-700",
    border: "border-purple-300",
    light: "bg-purple-50",
    badge: "bg-purple-100 text-purple-700",
  },
  expired: {
    bg: "bg-red-100",
    text: "text-red-600",
    border: "border-red-300",
    light: "bg-red-50",
    badge: "bg-red-100 text-red-600",
  },
};

export const getPlanColor = (plan, variant = "bg") => {
  const normalized = normalizePlan(plan);
  return PLAN_COLORS[normalized]?.[variant] || PLAN_COLORS.free[variant];
};

export const PLAN_BENEFITS = {
  cazador: [
    "Descripciones completas",
    "Match score real",
    "Análisis IA de contratos",
    "Alertas ilimitadas",
  ],
  competidor: [
    "Todo de Cazador +",
    "Pipeline CRM completo",
    "Scoring avanzado",
    "Tags personalizados",
    "Exportar a Excel",
  ],
  dominador: [
    "Todo de Competidor +",
    "Marketplace de contratos",
    "Análisis predictivo IA",
    "Soporte prioritario",
    "Múltiples usuarios",
  ],
};

export const FOMO_MESSAGES = {
  cazador: "Desbloquea descripciones completas y match score real",
  competidor: "Activa tu Pipeline CRM y scoring avanzado",
  dominador: "Accede al Marketplace y análisis predictivo IA",
};

// Badge component color mapping (for Badge color prop)
export const BADGE_COLORS = {
  free: "gray",
  trial: "blue",
  cazador: "green",
  competidor: "purple",
  dominador: "yellow",
  // Legacy aliases
  alertas: "green",
  starter: "green",
  business: "purple",
  enterprise: "yellow",
  expired: "red",
};

export const getBadgeColor = (plan) => {
  const normalized = normalizePlan(plan);
  return BADGE_COLORS[normalized] || BADGE_COLORS.free;
};
