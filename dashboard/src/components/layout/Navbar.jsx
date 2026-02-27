import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useApi } from "../../hooks/useApi";
import { List, X, Bell, SignOut, ArrowRight } from "@phosphor-icons/react";
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

// Nav items for mobile
const MOBILE_NAV = [
  ["/dashboard",   "Dashboard"],
  ["/contracts",   "Contratos"],
  ["/favorites",   "Favoritos"],
  ["/pipeline",    "Pipeline CRM"],
  ["/marketplace", "Marketplace"],
  ["/referrals",   "Referidos"],
  ["/payments",    "Plan"],
  ["/support",     "Soporte"],
  ["/settings",    "Configuración"],
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const [showNotifs, setShowNotifs] = useState(false);
  const { user, logout } = useAuth();

  return (
    <header className="lg:hidden sticky top-0 z-30 bg-white border-b border-surface-border">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setOpen(!open)}
            className="p-1.5 rounded-xl text-ink-600 hover:bg-surface-hover transition-colors"
          >
            {open ? <X size={20} /> : <List size={20} />}
          </button>
          <div className="flex items-center gap-2">
            <Logo size={26} />
            <span className="text-sm font-bold text-ink-900 tracking-tighter">Jobper</span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <div className="relative">
            <button
              onClick={() => setShowNotifs((v) => !v)}
              className="p-2 rounded-xl text-ink-500 hover:bg-surface-hover transition-colors"
            >
              <Bell size={18} weight="regular" />
            </button>
            {showNotifs && <NotificationPanel onClose={() => setShowNotifs(false)} />}
          </div>
          <button onClick={logout} className="p-2 rounded-xl text-ink-500 hover:bg-surface-hover transition-colors">
            <SignOut size={18} />
          </button>
        </div>
      </div>

      {open && (
        <nav className="border-t border-surface-border px-3 py-3 grid grid-cols-2 gap-1">
          {MOBILE_NAV.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `block px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand-50 text-brand-600 font-semibold"
                    : "text-ink-600 hover:bg-surface-hover hover:text-ink-900"
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      )}
    </header>
  );
}
