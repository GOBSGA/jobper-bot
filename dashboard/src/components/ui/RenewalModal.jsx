import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import Modal from "./Modal";
import Button from "./Button";
import { ArrowClockwise, ArrowsDownUp, X, Warning } from "@phosphor-icons/react";
import { date } from "../../lib/format";

export default function RenewalModal({ onClose }) {
  const navigate = useNavigate();
  const { subscription } = useAuth();

  const daysLeft = subscription?.days_remaining ?? 0;
  const planName = subscription?.plan || "";
  const expired = daysLeft <= 0;

  return (
    <Modal open={true} onClose={onClose} title={expired ? "Tu plan expiró" : "Tu plan está por vencer"}>
      <div className="space-y-4">
        <div className="border-l-2 border-amber-400 bg-amber-50/60 border border-surface-border rounded-xl p-4 flex gap-3">
          <Warning size={18} weight="duotone" className="text-amber-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-ink-700 leading-relaxed">
            {expired ? (
              <>Tu plan <strong>{planName}</strong> ha expirado. Acceso limitado al plan gratuito.</>
            ) : (
              <>Tu plan <strong>{planName}</strong> vence {daysLeft === 1 ? "mañana" : `en ${daysLeft} días`}{subscription?.ends_at && <> ({date(subscription.ends_at)})</>}.</>
            )}
          </p>
        </div>

        <div className="space-y-2">
          <Button className="w-full justify-center" onClick={() => { onClose(); navigate("/payments"); }}>
            <ArrowClockwise size={15} />
            {expired ? "Reactivar mi plan" : "Renovar mi plan"}
          </Button>
          <Button className="w-full justify-center" variant="secondary" onClick={() => { onClose(); navigate("/payments"); }}>
            <ArrowsDownUp size={15} />
            Cambiar de plan
          </Button>
          <button
            onClick={onClose}
            className="w-full text-xs text-ink-400 hover:text-ink-600 py-2 text-center transition-colors"
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
    <div className="mx-4 lg:mx-8 mt-4">
      <div className="bg-amber-50 border border-amber-200 rounded-2xl px-4 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5 min-w-0">
          <Warning size={16} weight="duotone" className="text-amber-500 flex-shrink-0" />
          <p className="text-xs text-amber-800 truncate">
            Tu plan vence {daysLeft === 1 ? "mañana" : `en ${daysLeft} días`}. Renueva para no perder acceso.
          </p>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <Button size="sm" onClick={onRenew}>Renovar</Button>
          <button onClick={() => setDismissed(true)} className="p-1.5 hover:bg-amber-100 rounded-lg transition-colors">
            <X size={13} className="text-amber-600" />
          </button>
        </div>
      </div>
    </div>
  );
}
