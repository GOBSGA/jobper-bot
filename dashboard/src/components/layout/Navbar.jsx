import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useApi } from "../../hooks/useApi";
import { X, Bell, ArrowRight } from "@phosphor-icons/react";
import { date, money } from "../../lib/format";
import Logo from "../ui/Logo";

function NotificationPanel({ onClose }) {
  const { data, loading } = useApi("/contracts/alerts?hours=48");
  const contracts = data?.contracts || [];

  return (
    <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-2xl border border-surface-border shadow-md z-50 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
        <p className="text-xs font-bold text-ink-900">Notificaciones</p>
        <button onClick={onClose} className="text-ink-400 hover:text-ink-600 transition-colors p-0.5 rounded">
          <X size={15} />
        </button>
      </div>
      <div className="max-h-72 overflow-y-auto divide-y divide-surface-border">
        {loading && <p className="text-xs text-ink-400 text-center py-6">Cargando...</p>}
        {!loading && contracts.length === 0 && (
          <p className="text-xs text-ink-400 text-center py-6">Sin contratos nuevos en 48 h.</p>
        )}
        {contracts.map((c) => (
          <a
            key={c.id}
            href={`/contracts/${c.id}`}
            className="block px-4 py-3 hover:bg-surface-hover transition-colors"
            onClick={onClose}
          >
            <p className="text-sm font-medium text-ink-900 line-clamp-1 leading-snug">{c.title}</p>
            <div className="flex items-center justify-between mt-1">
              <span className="text-2xs text-ink-400">{c.source}</span>
              <span className="text-2xs font-bold text-brand-500">{money(c.amount)}</span>
            </div>
            {c.deadline && (
              <p className="text-2xs text-ink-400 mt-0.5">Cierra: {date(c.deadline)}</p>
            )}
          </a>
        ))}
      </div>
      {contracts.length > 0 && (
        <div className="px-4 py-3 border-t border-surface-border">
          <a href="/contracts" className="flex items-center gap-1 text-xs text-brand-500 hover:text-brand-700 font-medium">
            Ver todos <ArrowRight size={11} />
          </a>
        </div>
      )}
    </div>
  );
}

export default function Navbar() {
  const [showNotifs, setShowNotifs] = useState(false);

  return (
    <header className="lg:hidden sticky top-0 z-30 bg-white border-b border-surface-border">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <Logo size={26} />
          <span className="text-sm font-bold text-ink-900 tracking-tighter">Jobper</span>
        </div>
        <div className="relative">
          <button
            onClick={() => setShowNotifs((v) => !v)}
            className="p-2 rounded-xl text-ink-500 hover:bg-surface-hover transition-colors"
          >
            <Bell size={18} weight="regular" />
          </button>
          {showNotifs && <NotificationPanel onClose={() => setShowNotifs(false)} />}
        </div>
      </div>
    </header>
  );
}
