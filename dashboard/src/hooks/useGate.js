import { useAuth } from "../context/AuthContext";

const PLAN_ORDER = { free: 0, trial: 1, alertas: 2, starter: 2, business: 3, enterprise: 4 };

const FEATURE_GATES = {
  full_description: "alertas",
  match_scores: "alertas",
  alerts: "alertas",
  favorites: "alertas",
  match: "alertas",
  email_digest: "alertas",
  advanced_filters: "alertas",
  export: "alertas",
  ai_analysis: "business",
  pipeline: "business",
  marketplace: "business",
  push: "business",
  documents: "business",
  reports: "business",
  team: "enterprise",
  competitive_intelligence: "enterprise",
  api_access: "enterprise",
  priority_support: "enterprise",
};

export function useGate(feature) {
  const { user } = useAuth();
  const userPlan = user?.plan || "free";
  const requiredPlan = FEATURE_GATES[feature];

  if (!requiredPlan) return { allowed: true, requiredPlan: null };

  const userLevel = PLAN_ORDER[userPlan] ?? 0;
  const requiredLevel = PLAN_ORDER[requiredPlan] ?? 0;

  return {
    allowed: userLevel >= requiredLevel,
    requiredPlan,
    currentPlan: userPlan,
  };
}
