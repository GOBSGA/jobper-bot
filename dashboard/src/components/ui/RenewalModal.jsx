import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import Modal from "./Modal";
import Button from "./Button";
import { RefreshCw, ArrowUpDown, X, AlertTriangle } from "lucide-react";
import { date } from "../../lib/format";

export default function RenewalModal({ onClose }) {
  const navigate = useNavigate();
  const { subscription } = useAuth();

  const handleRenew = () => {
    onClose();
    navigate("/payments");
  };

  const handleChangePlan = () => {
    onClose();
    navigate("/payments");
  };

  const handleContinueFree = () => {
    onClose();
  };

  const daysLeft = subscription?.days_remaining ?? 0;
  const planName = subscription?.plan || "";
  const expired = daysLeft <= 0;

  return (
    <Modal open={true} onClose={onClose} title={expired ? "Tu plan expiró" : "Tu plan está por vencer"}>
      <div className="space-y-5">
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            {expired ? (
              <p className="text-sm text-amber-800">
                Tu plan <strong>{planName}</strong> ha expirado. Tu cuenta ahora está en el plan gratuito con funcionalidades limitadas.
              </p>
            ) : (
              <p className="text-sm text-amber-800">
                Tu plan <strong>{planName}</strong> vence {daysLeft === 1 ? "mañana" : `en ${daysLeft} días`}
                {subscription?.ends_at && <> ({date(subscription.ends_at)})</>}.
                Renueva para no perder acceso.
              </p>
            )}
          </div>
        </div>

        <div className="space-y-3">
          <Button className="w-full justify-center" onClick={handleRenew}>
            <RefreshCw className="h-4 w-4" />
            {expired ? "Reactivar mi plan" : "Renovar mi plan"}
          </Button>

          <Button className="w-full justify-center" variant="secondary" onClick={handleChangePlan}>
            <ArrowUpDown className="h-4 w-4" />
            Cambiar de plan
          </Button>

          <button
            onClick={handleContinueFree}
            className="w-full text-sm text-gray-400 hover:text-gray-600 hover:underline py-2 text-center transition"
          >
            Continuar con plan gratuito
          </button>
        </div>
      </div>
    </Modal>
  );
}

export function RenewalBanner({ daysLeft, onRenew }) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="mx-4 lg:mx-8 mt-4 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0" />
        <p className="text-sm text-amber-800 truncate">
          Tu plan vence {daysLeft === 1 ? "mañana" : `en ${daysLeft} días`}. Renueva para no perder acceso.
        </p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <Button size="sm" onClick={onRenew}>Renovar</Button>
        <button onClick={() => setDismissed(true)} className="p-1 hover:bg-amber-100 rounded-lg transition">
          <X className="h-4 w-4 text-amber-600" />
        </button>
      </div>
    </div>
  );
}
