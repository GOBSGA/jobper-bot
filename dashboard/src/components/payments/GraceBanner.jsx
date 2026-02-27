import { Warning } from "@phosphor-icons/react";
import { useCountdown } from "../../hooks/useCountdown";

/**
 * Grace period banner: shows countdown timer while payment is pending admin approval.
 * Backend grants 24h grace — aligned here.
 */
export default function GraceBanner({ graceUntil, plan }) {
  const countdown = useCountdown(graceUntil);

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
      <Warning size={18} weight="duotone" className="text-amber-500 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-semibold text-amber-900">Acceso temporal activo — Plan {plan}</p>
          {countdown && (
            <span className="bg-amber-200 text-amber-900 text-2xs px-2 py-0.5 rounded-full font-bold">
              {countdown} restantes
            </span>
          )}
        </div>
        <p className="text-xs text-amber-700 mt-1 leading-relaxed">
          Tu pago está siendo verificado. Tienes acceso completo mientras lo confirmamos (máx. 24h).
          Si el pago es válido, tu plan se activa por 30 días completos.
        </p>
      </div>
    </div>
  );
}
