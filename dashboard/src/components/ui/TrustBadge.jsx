import { Shield, CheckCircle, Star, Crown, Award } from "lucide-react";

const TRUST_LEVELS = {
  new: {
    label: "Nuevo",
    color: "text-gray-400 bg-gray-100",
    icon: null,
    description: "Aún no tienes pagos verificados",
  },
  bronze: {
    label: "Bronce",
    color: "text-amber-700 bg-amber-100 border-amber-200",
    icon: Shield,
    description: "1 pago verificado",
  },
  silver: {
    label: "Plata",
    color: "text-gray-600 bg-gray-200 border-gray-300",
    icon: CheckCircle,
    description: "2+ pagos verificados • Renovación 1-clic",
  },
  gold: {
    label: "Oro",
    color: "text-yellow-700 bg-yellow-100 border-yellow-300",
    icon: Star,
    description: "4+ pagos verificados • Cliente leal",
  },
  platinum: {
    label: "Platino",
    color: "text-purple-700 bg-purple-100 border-purple-300",
    icon: Crown,
    description: "8+ pagos verificados • VIP",
  },
};

export function TrustBadge({ level = "new", showLabel = true, size = "md" }) {
  const config = TRUST_LEVELS[level] || TRUST_LEVELS.new;
  const Icon = config.icon;

  const sizeClasses = {
    sm: "text-xs px-1.5 py-0.5",
    md: "text-sm px-2 py-1",
    lg: "text-base px-3 py-1.5",
  };

  const iconSizes = {
    sm: "h-3 w-3",
    md: "h-4 w-4",
    lg: "h-5 w-5",
  };

  if (level === "new") return null;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium border ${config.color} ${sizeClasses[size]}`}
      title={config.description}
    >
      {Icon && <Icon className={iconSizes[size]} />}
      {showLabel && config.label}
    </span>
  );
}

export function TrustCard({ trustInfo, className = "" }) {
  if (!trustInfo) return null;

  const config = TRUST_LEVELS[trustInfo.trust_level] || TRUST_LEVELS.new;
  const Icon = config.icon || Award;

  const progress = Math.min(100, (trustInfo.trust_score / 50) * 100);

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-4 ${className}`}>
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg ${config.color}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">Pagador Verificado</h3>
          <p className="text-sm text-gray-500">{config.description}</p>
        </div>
      </div>

      {/* Trust Progress */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Puntos de confianza</span>
          <span className="font-medium text-gray-900">{trustInfo.trust_score?.toFixed(0) || 0}</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-brand-500 to-purple-500 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-400">
          <span>Nuevo</span>
          <span>Bronce</span>
          <span>Plata</span>
          <span>Oro</span>
          <span>Platino</span>
        </div>
      </div>

      {/* Stats */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-gray-900">{trustInfo.verified_payments_count || 0}</p>
          <p className="text-xs text-gray-500">Pagos verificados</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-gray-900">
            {trustInfo.one_click_renewal_enabled ? (
              <CheckCircle className="h-8 w-8 text-green-500 mx-auto" />
            ) : (
              <span className="text-gray-400">—</span>
            )}
          </p>
          <p className="text-xs text-gray-500">Renovación 1-clic</p>
        </div>
      </div>

      {/* One-click renewal hint */}
      {!trustInfo.one_click_renewal_enabled && (
        <p className="mt-3 text-xs text-center text-gray-400">
          {2 - (trustInfo.verified_payments_count || 0)} pago(s) más para desbloquear renovación 1-clic
        </p>
      )}
    </div>
  );
}

export function TrustRewardToast({ rewards }) {
  if (!rewards || rewards.length === 0) return null;

  return (
    <div className="space-y-2">
      {rewards.map((reward, i) => (
        <div key={i} className="flex items-center gap-2">
          {reward.type === "level_up" && (
            <>
              <Star className="h-5 w-5 text-yellow-500" />
              <span className="font-medium">{reward.message}</span>
            </>
          )}
          {reward.type === "feature_unlock" && (
            <>
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="font-medium">{reward.message}</span>
            </>
          )}
        </div>
      ))}
    </div>
  );
}

export default TrustBadge;
