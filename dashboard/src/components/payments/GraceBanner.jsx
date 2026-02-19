import { AlertCircle } from "lucide-react";
import { useCountdown } from "../../hooks/useCountdown";

/**
 * Grace period banner: shows countdown timer while payment is pending admin approval
 */
export default function GraceBanner({ graceUntil, plan }) {
  const countdown = useCountdown(graceUntil);

  return (
    <div className="bg-amber-50 border-2 border-amber-300 rounded-lg p-4 flex items-start gap-3">
      <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <p className="font-semibold text-amber-800">Acceso temporal activo — Plan {plan}</p>
          <span className="bg-amber-200 text-amber-900 text-xs px-2 py-0.5 rounded-full font-bold">
            {countdown} restantes
          </span>
        </div>
        <p className="text-sm text-amber-700 mt-1">
          Tu pago está siendo verificado. Tienes acceso completo mientras lo confirmamos (máx. 24h).
          Si el pago es válido, tu plan se activa por 30 días completos sin que tengas que hacer nada.
        </p>
      </div>
    </div>
  );
}
