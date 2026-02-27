import { Check, X, Lightning, ArrowRight } from "@phosphor-icons/react";
import Card from "../ui/Card";
import Button from "../ui/Button";
import { money } from "../../lib/format";

/**
 * Plan card — calm, flat, no gradient backgrounds.
 * Popular plan uses a subtle ring, not a garish gradient.
 */
export default function PlanCard({ plan, currentPlan, onSelect, isDowngrade }) {
  const isCurrent = currentPlan === plan.key;

  return (
    <Card
      className={`relative flex flex-col p-6 ${
        plan.popular
          ? "ring-1 ring-brand-300 border-brand-200"
          : ""
      }`}
    >
      {/* Popular badge */}
      {plan.popular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="inline-flex items-center gap-1 bg-brand-500 text-white rounded-full px-3 py-1 text-2xs font-semibold tracking-snug shadow-sm">
            <Lightning size={10} weight="fill" /> Más popular
          </span>
        </div>
      )}

      <div className="flex-1 space-y-5">
        {/* Header */}
        <div className="text-center pt-1">
          <div className="inline-flex items-center justify-center w-11 h-11 rounded-2xl bg-surface-hover mb-3">
            <span className="text-2xl leading-none">{plan.emoji}</span>
          </div>
          <h3 className="text-base font-bold text-ink-900 tracking-snug">{plan.displayName}</h3>
          <p className="text-xs text-ink-400 mt-1 leading-relaxed">{plan.tagline}</p>
        </div>

        {/* Price */}
        <div className="text-center">
          {plan.price === 0 ? (
            <p className="text-2xl font-bold text-ink-900 tracking-tighter">Gratis</p>
          ) : (
            <>
              <p className="text-2xl font-bold text-ink-900 tracking-tighter">
                {money(plan.price)}
                <span className="text-sm font-normal text-ink-400">/mes</span>
              </p>
              <p className="text-2xs text-ink-400 mt-0.5">{money(plan.price * 12)}/año</p>
            </>
          )}
        </div>

        {/* Features */}
        <ul className="space-y-2">
          {plan.features.map((f, i) => (
            <li
              key={i}
              className={`flex items-start gap-2 text-xs leading-relaxed ${
                f.included ? "text-ink-700" : "text-ink-200"
              }`}
            >
              {f.included ? (
                <Check
                  size={14}
                  weight="bold"
                  className={`flex-shrink-0 mt-0.5 ${
                    f.highlight ? "text-accent-600" : "text-ink-300"
                  }`}
                />
              ) : (
                <X size={14} weight="bold" className="flex-shrink-0 mt-0.5 text-ink-200" />
              )}
              <span className={f.highlight ? "font-medium text-ink-800" : ""}>{f.text}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* CTA */}
      <div className="pt-5 mt-5 border-t border-surface-border">
        {isCurrent ? (
          <Button className="w-full justify-center" variant="secondary" disabled>
            <Check size={14} /> Plan actual
          </Button>
        ) : plan.price === 0 ? (
          <Button className="w-full justify-center" variant="secondary" disabled>
            Plan gratuito
          </Button>
        ) : isDowngrade ? (
          <Button className="w-full justify-center" variant="secondary" disabled>
            Plan inferior al tuyo
          </Button>
        ) : (
          <Button
            className="w-full justify-center"
            onClick={() => onSelect(plan)}
          >
            Activar {plan.displayName}
            <ArrowRight size={14} />
          </Button>
        )}
      </div>
    </Card>
  );
}
