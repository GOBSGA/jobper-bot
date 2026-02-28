import { useApi } from "../../hooks/useApi";
import Card, { CardHeader } from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { useToast } from "../../components/ui/Toast";
import {
  Users,
  Copy,
  Gift,
  ChatCircle,
  ShareNetwork,
  EnvelopeSimple,
  CheckCircle,
  Lock,
  WhatsappLogo,
} from "@phosphor-icons/react";

export default function Referrals() {
  const { data, loading } = useApi("/referrals/");
  const toast = useToast();

  const code = data?.code || "";
  const referralUrl = code
    ? `${window.location.origin}/register?ref=${code}`
    : `${window.location.origin}/register`;

  const copy = () => {
    if (!referralUrl) return;
    navigator.clipboard.writeText(referralUrl);
    toast.success("Link copiado al portapapeles");
  };

  const shareWhatsApp = () => {
    const text = encodeURIComponent(
      `Encontré Jobper, una plataforma que te muestra todos los contratos del gobierno que puedes ganar. Regístrate gratis: ${referralUrl}`
    );
    window.open(`https://wa.me/?text=${text}`, "_blank");
  };

  const shareEmail = () => {
    const subject = encodeURIComponent("Te recomiendo Jobper para contratos públicos");
    const body = encodeURIComponent(
      `Hola,\n\nQuiero compartirte Jobper, una plataforma que te ayuda a encontrar y ganar contratos del gobierno colombiano.\n\nRegístrate gratis acá: ${referralUrl}\n\nSaludos`
    );
    window.open(`mailto:?subject=${subject}&body=${body}`);
  };

  if (loading)
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    );

  const signups = data?.total_signups ?? 0;
  const referralsNeeded = Math.max(0, 3 - signups);

  const TIERS = [
    { refs: 1, reward: "10% descuento en tu suscripción" },
    { refs: 3, reward: "1 mes gratis plan Alertas" },
    { refs: 5, reward: "30% descuento permanente" },
    { refs: 10, reward: "50% descuento permanente" },
  ];

  return (
    <div className="space-y-6 pb-8">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-ink-900">Programa de referidos</h1>
        <p className="text-sm text-ink-400 mt-1">
          Invita amigos y gana recompensas exclusivas
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ── Left column ── */}
        <div className="space-y-5">
          {/* Hero CTA */}
          <Card className="p-6 bg-gradient-to-br from-accent-50 to-brand-50 border-accent-100">
            <div className="text-center space-y-3">
              <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-white shadow-sm mx-auto">
                <Gift size={28} className="text-accent-600" weight="duotone" />
              </div>
              <h2 className="text-xl font-bold text-ink-900">Invita 3 amigos = 1 mes gratis</h2>
              <p className="text-sm text-ink-600 max-w-sm mx-auto">
                Comparte tu link. Cuando 3 amigos se registren, recibes 1 mes del plan Alertas
                ($29,900 COP) completamente gratis.
              </p>
              {referralsNeeded > 0 ? (
                <div className="inline-flex items-center gap-2 bg-white rounded-full px-4 py-1.5 text-sm font-semibold text-brand-600 shadow-sm">
                  <Users size={14} />
                  Te faltan {referralsNeeded}{" "}
                  {referralsNeeded === 1 ? "referido" : "referidos"} para tu mes gratis
                </div>
              ) : (
                <Badge color="green" className="text-sm">
                  ✓ Ya ganaste tu mes gratis
                </Badge>
              )}
            </div>
          </Card>

          {/* Share link */}
          <Card className="p-5">
            <h2 className="font-semibold text-ink-900 mb-4">Comparte tu link</h2>
            <div className="flex items-center gap-2 mb-4">
              <code className="flex-1 bg-surface-hover px-4 py-2.5 rounded-xl border border-surface-border text-sm font-mono truncate text-ink-600">
                {referralUrl || "Cargando..."}
              </code>
              <Button size="sm" onClick={copy} disabled={!code}>
                <Copy size={14} /> Copiar
              </Button>
            </div>
            <div className="grid grid-cols-3 gap-2.5">
              <button
                onClick={shareWhatsApp}
                disabled={!code}
                className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-[#25D366] hover:bg-[#20BC5A] text-white text-sm font-medium transition disabled:opacity-50"
              >
                <WhatsappLogo size={16} weight="fill" /> WhatsApp
              </button>
              <Button onClick={shareEmail} disabled={!code} variant="secondary" className="text-sm">
                <EnvelopeSimple size={14} /> Email
              </Button>
              <Button onClick={copy} disabled={!code} variant="secondary" className="text-sm">
                <ShareNetwork size={14} /> Copiar
              </Button>
            </div>
          </Card>
        </div>

        {/* ── Right column ── */}
        <div className="space-y-5">
          {/* Stats */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Clicks", value: data?.total_clicks ?? 0, color: "text-brand-600 bg-brand-50" },
              { label: "Registros", value: data?.total_signups ?? 0, color: "text-accent-600 bg-accent-50" },
              { label: "Suscritos", value: data?.total_subscribed ?? 0, color: "text-purple-600 bg-purple-50" },
              {
                label: "Descuento actual",
                value: `${Math.round((data?.current_discount ?? 0) * 100)}%`,
                color: "text-amber-600 bg-amber-50",
              },
            ].map((s) => (
              <Card key={s.label} className="p-4 text-center">
                <p className={`text-2xl font-bold ${s.color.split(" ")[0]}`}>{s.value}</p>
                <p className="text-xs text-ink-400 mt-1">{s.label}</p>
              </Card>
            ))}
          </div>

          {/* Reward tiers */}
          <Card className="p-5">
            <h2 className="font-semibold text-ink-900 mb-4">Recompensas por referidos</h2>
            <div className="space-y-2.5">
              {TIERS.map((tier) => {
                const unlocked = signups >= tier.refs;
                return (
                  <div
                    key={tier.refs}
                    className={`flex items-center gap-3 p-3.5 rounded-xl border transition ${
                      unlocked
                        ? "bg-accent-50 border-accent-100"
                        : "bg-surface-hover border-surface-border"
                    }`}
                  >
                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                        unlocked ? "bg-accent-500 text-white" : "bg-surface-border text-ink-400"
                      }`}
                    >
                      {unlocked ? (
                        <CheckCircle size={18} weight="fill" />
                      ) : (
                        tier.refs
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p
                        className={`text-sm font-medium ${
                          unlocked ? "text-ink-900" : "text-ink-600"
                        }`}
                      >
                        {tier.reward}
                      </p>
                      <p className="text-xs text-ink-400">
                        {tier.refs} {tier.refs === 1 ? "referido" : "referidos"}
                      </p>
                    </div>
                    {unlocked && <Badge color="green">Desbloqueado</Badge>}
                    {!unlocked && (
                      <Lock size={14} className="text-ink-300 flex-shrink-0" />
                    )}
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
