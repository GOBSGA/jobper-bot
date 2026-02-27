import { Copy } from "@phosphor-icons/react";

/**
 * Reusable payment method box
 */
export default function PaymentMethodBox({
  color = "brand",
  title,
  subtitle,
  value,
  footer,
  recommended,
  onCopy,
}) {
  const colorClasses = {
    brand: {
      bg: "bg-brand-50",
      border: "border-brand-300",
      borderLight: "border-brand-200",
      text: "text-brand-600",
      textDark: "text-brand-900",
      textLight: "text-brand-600",
      badge: "bg-brand-100 text-brand-700",
      hoverBg: "hover:bg-brand-100",
    },
    accent: {
      bg: "bg-accent-50",
      border: "border-accent-300",
      borderLight: "border-accent-200",
      text: "text-accent-700",
      textDark: "text-accent-900",
      textLight: "text-accent-700",
      badge: "bg-accent-100 text-accent-700",
      hoverBg: "hover:bg-accent-100",
    },
    amber: {
      bg: "bg-amber-50",
      border: "border-amber-300",
      borderLight: "border-amber-200",
      text: "text-amber-700",
      textDark: "text-amber-900",
      textLight: "text-amber-700",
      badge: "bg-amber-100 text-amber-700",
      hoverBg: "hover:bg-amber-100",
    },
  };

  const c = colorClasses[color] || colorClasses.brand;

  return (
    <div
      className={`${c.bg} ${recommended ? `border-2 ${c.border}` : `border ${c.borderLight}`} rounded-2xl p-4`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold ${c.text} uppercase tracking-wide`}>{title}</span>
            {recommended && (
              <span className={`${c.badge} text-2xs px-2 py-0.5 rounded-full font-semibold`}>
                Recomendado
              </span>
            )}
          </div>
          {subtitle && <p className={`text-xs ${c.textLight} mb-1`}>{subtitle}</p>}
          <p className={`text-xl ${c.textDark} font-mono font-bold tracking-wide`}>{value}</p>
          {footer && <p className={`text-xs ${c.textLight} mt-1`}>{footer}</p>}
        </div>
        <button
          onClick={() => onCopy(value)}
          className={`p-2 ${c.hoverBg} rounded-xl transition flex-shrink-0 ml-3`}
          title="Copiar"
        >
          <Copy size={15} className={c.text} />
        </button>
      </div>
    </div>
  );
}
