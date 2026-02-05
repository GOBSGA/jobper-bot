import { useApi } from "../../hooks/useApi";
import { useAuth } from "../../context/AuthContext";
import Card, { CardHeader } from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { useToast } from "../../components/ui/Toast";
import { Users, Copy, Gift, MessageCircle, Share2, Mail } from "lucide-react";

export default function Referrals() {
  const { user } = useAuth();
  const { data, loading } = useApi("/referrals/stats");
  const toast = useToast();

  const referralUrl = `${window.location.origin}/login?ref=${user?.referral_code}`;

  const copy = () => {
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

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;

  const stats = data || {};
  const referralsNeeded = Math.max(0, 3 - (stats.signups || 0));

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Programa de referidos</h1>

      {/* Main CTA */}
      <Card className="bg-gradient-to-r from-green-50 to-brand-50 border-green-200">
        <div className="text-center space-y-4">
          <Gift className="h-12 w-12 text-green-600 mx-auto" />
          <h2 className="text-xl font-bold text-gray-900">Invita 3 amigos = 1 mes gratis</h2>
          <p className="text-sm text-gray-600">
            Comparte tu link. Cuando 3 amigos se registren, recibes 1 mes del plan Alertas ($29,900 COP) completamente gratis.
          </p>
          {referralsNeeded > 0 ? (
            <p className="text-sm font-semibold text-brand-600">
              Te faltan {referralsNeeded} {referralsNeeded === 1 ? "referido" : "referidos"} para tu mes gratis
            </p>
          ) : (
            <Badge color="green" className="text-sm">Ya ganaste tu mes gratis</Badge>
          )}
        </div>
      </Card>

      {/* Share buttons */}
      <Card>
        <CardHeader title="Comparte tu link" />
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <code className="flex-1 bg-gray-50 px-4 py-3 rounded-lg border text-sm font-mono truncate">{referralUrl}</code>
            <Button size="sm" onClick={copy}><Copy className="h-4 w-4" /> Copiar</Button>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <Button onClick={shareWhatsApp} className="bg-green-600 hover:bg-green-700 text-white">
              <MessageCircle className="h-4 w-4" /> WhatsApp
            </Button>
            <Button onClick={shareEmail} variant="secondary">
              <Mail className="h-4 w-4" /> Email
            </Button>
            <Button onClick={copy} variant="secondary">
              <Share2 className="h-4 w-4" /> Copiar link
            </Button>
          </div>
        </div>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Clicks", value: stats.clicks ?? 0 },
          { label: "Registros", value: stats.signups ?? 0 },
          { label: "Suscritos", value: stats.subscribed ?? 0 },
          { label: "Descuento actual", value: `${stats.discount ?? 0}%` },
        ].map((s) => (
          <Card key={s.label} className="text-center">
            <p className="text-2xl font-bold text-gray-900">{s.value}</p>
            <p className="text-xs text-gray-500 mt-1">{s.label}</p>
          </Card>
        ))}
      </div>

      {/* Rewards tiers */}
      <Card>
        <CardHeader title="Recompensas por referidos" />
        <div className="space-y-3">
          {[
            { refs: 1, reward: "10% descuento en tu suscripción" },
            { refs: 3, reward: "1 mes gratis plan Alertas" },
            { refs: 5, reward: "30% descuento permanente" },
            { refs: 10, reward: "50% descuento permanente" },
          ].map((tier) => (
            <div key={tier.refs} className={`flex items-center justify-between p-3 rounded-lg ${
              (stats.signups || 0) >= tier.refs ? "bg-green-50 border border-green-200" : "bg-gray-50"
            }`}>
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  (stats.signups || 0) >= tier.refs ? "bg-green-600 text-white" : "bg-gray-300 text-white"
                }`}>
                  {tier.refs}
                </div>
                <span className="text-sm font-medium text-gray-900">{tier.reward}</span>
              </div>
              {(stats.signups || 0) >= tier.refs && (
                <Badge color="green">Desbloqueado</Badge>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
