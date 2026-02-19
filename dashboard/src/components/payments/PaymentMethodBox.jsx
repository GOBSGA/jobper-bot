import { Copy } from "lucide-react";

/**
 * Reusable payment method box
 * @param {string} color - Color theme (green, purple, yellow)
 * @param {string} title - Payment method title
 * @param {string} subtitle - Optional subtitle/type
 * @param {string} value - Account number/handle to display
 * @param {string} footer - Optional footer text
 * @param {boolean} recommended - Show recommended badge
 * @param {function} onCopy - Callback when copy button clicked
 */
export default function PaymentMethodBox({
  color = "green",
  title,
  subtitle,
  value,
  footer,
  recommended,
  onCopy,
}) {
  const colorClasses = {
    green: {
      bg: "bg-green-50",
      border: "border-green-400",
      borderLight: "border-green-200",
      text: "text-green-700",
      textDark: "text-green-900",
      textLight: "text-green-700",
      badge: "bg-green-200 text-green-800",
      hoverBg: "hover:bg-green-100",
    },
    purple: {
      bg: "bg-purple-50",
      border: "border-purple-200",
      borderLight: "border-purple-200",
      text: "text-purple-600",
      textDark: "text-purple-800",
      textLight: "text-purple-700",
      badge: "bg-purple-200 text-purple-800",
      hoverBg: "hover:bg-purple-100",
    },
    yellow: {
      bg: "bg-yellow-50",
      border: "border-yellow-200",
      borderLight: "border-yellow-200",
      text: "text-yellow-600",
      textDark: "text-yellow-800",
      textLight: "text-yellow-700",
      badge: "bg-yellow-200 text-yellow-800",
      hoverBg: "hover:bg-yellow-100",
    },
  };

  const c = colorClasses[color];

  return (
    <div
      className={`${c.bg} ${recommended ? `border-2 ${c.border}` : `border ${c.borderLight}`} rounded-lg p-4`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold ${c.text} uppercase tracking-wide`}>{title}</span>
            {recommended && (
              <span className={`${c.badge} text-xs px-2 py-0.5 rounded-full font-medium`}>
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
          className={`p-2 ${c.hoverBg} rounded-lg transition flex-shrink-0`}
          title="Copiar"
        >
          <Copy className={`h-4 w-4 ${c.text}`} />
        </button>
      </div>
    </div>
  );
}
