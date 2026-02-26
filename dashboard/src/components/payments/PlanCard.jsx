import { Check, X, Zap, ChevronRight } from "lucide-react";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import { money } from "../../lib/format";

/**
 * Individual plan card component
 */
export default function PlanCard({ plan, currentPlan, onSelect, isDowngrade }) {
  const Icon = plan.icon;
  const isCurrent = currentPlan === plan.key;

  return (
    <Card
      className={`relative flex flex-col ${
        plan.popular ? "ring-2 ring-purple-500 shadow-lg" : ""
      } ${plan.color === "amber" ? "bg-gradient-to-b from-amber-50 to-white" : ""} ${
        plan.color === "orange" ? "bg-gradient-to-b from-orange-50 to-white" : ""
      }`}
    >
      {/* Popular badge */}
      {plan.popular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Badge color="purple" className="shadow-md">
            <Zap className="h-3 w-3 mr-1" /> Más popular
          </Badge>
        </div>
      )}

      <div className="flex-1 space-y-4">
        {/* Header */}
        <div className="text-center pt-2">
          <div
            className={`inline-flex items-center justify-center w-12 h-12 rounded-full mb-3 ${
              plan.color === "gray" ? "bg-gray-100" : ""
            } ${plan.color === "blue" ? "bg-blue-100" : ""} ${
              plan.color === "purple" ? "bg-purple-100" : ""
            } ${plan.color === "amber" ? "bg-amber-100" : ""} ${
              plan.color === "orange" ? "bg-orange-100" : ""
            }`}
          >
            <Icon
              className={`h-6 w-6 ${plan.color === "gray" ? "text-gray-600" : ""} ${
                plan.color === "blue" ? "text-blue-600" : ""
              } ${plan.color === "purple" ? "text-purple-600" : ""} ${
                plan.color === "amber" ? "text-amber-600" : ""
              } ${plan.color === "orange" ? "text-orange-600" : ""}`}
            />
          </div>
          <div className="flex items-center justify-center gap-2">
            <span className="text-2xl">{plan.emoji}</span>
            <h3 className="text-xl font-bold text-gray-900">{plan.displayName}</h3>
          </div>
          <p className="text-sm text-gray-500 mt-1">{plan.tagline}</p>
        </div>

        {/* Price */}
        <div className="text-center py-2">
          {plan.price === 0 ? (
            <p className="text-3xl font-bold text-gray-900">Gratis</p>
          ) : (
            <div>
              <p className="text-3xl font-bold text-gray-900">
                {money(plan.price)}
                <span className="text-base font-normal text-gray-500">/mes</span>
              </p>
              <p className="text-xs text-gray-400 mt-1">{money(plan.price * 12)}/año</p>
            </div>
          )}
        </div>

        {/* Features */}
        <ul className="space-y-2.5 px-2">
          {plan.features.map((f, i) => (
            <li
              key={i}
              className={`flex items-start gap-2 text-sm ${
                f.included ? "text-gray-700" : "text-gray-400"
              }`}
            >
              {f.included ? (
                <Check
                  className={`h-4 w-4 flex-shrink-0 mt-0.5 ${
                    f.highlight ? "text-green-500" : "text-green-400"
                  }`}
                />
              ) : (
                <X className="h-4 w-4 flex-shrink-0 mt-0.5 text-gray-300" />
              )}
              <span className={f.highlight ? "font-medium" : ""}>{f.text}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* CTA Button */}
      <div className="pt-4 mt-4 border-t border-gray-100">
        {isCurrent ? (
          <Button className="w-full" variant="secondary" disabled>
            <Check className="h-4 w-4 mr-1" /> Plan actual
          </Button>
        ) : plan.price === 0 ? (
          <Button className="w-full" variant="secondary" disabled>
            Plan gratuito
          </Button>
        ) : isDowngrade ? (
          <Button className="w-full" variant="secondary" disabled>
            Ya tienes un plan superior
          </Button>
        ) : (
          <Button
            className={`w-full ${plan.color === "blue" ? "bg-blue-600 hover:bg-blue-700" : ""} ${
              plan.color === "purple" ? "bg-purple-600 hover:bg-purple-700" : ""
            } ${plan.color === "amber" ? "bg-amber-600 hover:bg-amber-700" : ""} ${
              plan.color === "orange" ? "bg-orange-600 hover:bg-orange-700" : ""
            }`}
            onClick={() => onSelect(plan)}
          >
            Activar {plan.displayName}
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        )}
      </div>
    </Card>
  );
}
