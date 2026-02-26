/**
 * Centralized plan configuration and utilities
 * Single source of truth for plan hierarchy, colors, and benefits
 */

export const PLAN_ORDER = {
  free: 0,
  trial: 0,
  cazador: 1,
  competidor: 2,
  estratega: 3,
  dominador: 4,
  // Legacy aliases
  alertas: 1,
  starter: 1,
  business: 2,
  enterprise: 4,
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
  estratega: {
    bg: "bg-orange-100",
    text: "text-orange-700",
    border: "border-orange-300",
    light: "bg-orange-50",
    badge: "bg-orange-100 text-orange-700",
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
  estratega: [
    "Todo de Competidor +",
    "2 usuarios en equipo",
    "Historial 2 años",
    "Reportes automáticos",
    "Soporte email prioritario",
  ],
  dominador: [
    "Todo de Estratega +",
    "Inteligencia competitiva",
    "5 usuarios en equipo",
    "Auto-propuestas con IA",
    "Consultoría mensual",
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
  estratega: "orange",
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
