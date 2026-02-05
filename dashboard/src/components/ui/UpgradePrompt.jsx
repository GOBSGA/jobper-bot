import { Link } from "react-router-dom";
import { Lock } from "lucide-react";

const PLAN_NAMES = {
  alertas: "Alertas",
  business: "Business",
  enterprise: "Enterprise",
};

export default function UpgradePrompt({ feature, requiredPlan, children }) {
  const planName = PLAN_NAMES[requiredPlan] || requiredPlan;

  return (
    <div className="relative">
      <div className="opacity-40 pointer-events-none select-none">{children}</div>
      <div className="absolute inset-0 flex items-center justify-center bg-white/60 backdrop-blur-[2px] rounded-lg">
        <div className="text-center px-4">
          <Lock className="h-6 w-6 text-gray-400 mx-auto mb-2" />
          <p className="text-sm font-semibold text-gray-700">
            Disponible en el plan {planName}
          </p>
          <Link
            to="/pricing"
            className="inline-block mt-2 px-4 py-1.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700"
          >
            Actualizar plan
          </Link>
        </div>
      </div>
    </div>
  );
}
