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
    bg: "bg-surface-hover",
    text: "text-ink-600",
    border: "border-surface-border",
    light: "bg-surface-bg",
    badge: "bg-surface-hover text-ink-600",
  },
  trial: {
    bg: "bg-brand-50",
    text: "text-brand-600",
    border: "border-brand-200",
    light: "bg-brand-50",
    badge: "bg-brand-50 text-brand-600",
  },
  cazador: {
    bg: "bg-accent-50",
    text: "text-accent-700",
    border: "border-accent-200",
    light: "bg-accent-50",
    badge: "bg-accent-50 text-accent-700",
  },
  competidor: {
    bg: "bg-brand-50",
    text: "text-brand-600",
    border: "border-brand-200",
    light: "bg-brand-50",
    badge: "bg-brand-50 text-brand-600",
  },
  estratega: {
    bg: "bg-violet-50",
    text: "text-violet-700",
    border: "border-violet-200",
    light: "bg-violet-50",
    badge: "bg-violet-50 text-violet-700",
  },
  dominador: {
    bg: "bg-slate-100",
    text: "text-slate-700",
    border: "border-slate-300",
    light: "bg-slate-50",
    badge: "bg-slate-100 text-slate-700",
  },
  expired: {
    bg: "bg-red-50",
    text: "text-red-600",
    border: "border-red-200",
    light: "bg-red-50",
    badge: "bg-red-50 text-red-600",
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
