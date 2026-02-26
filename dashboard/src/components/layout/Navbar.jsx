import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useApi } from "../../hooks/useApi";
import { Menu, X, Bell, LogOut } from "lucide-react";
import { date, money } from "../../lib/format";

function NotificationPanel({ onClose }) {
  const { data, loading } = useApi("/contracts/alerts?hours=48");
  const contracts = data?.contracts || [];

  return (
    <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-200 z-50">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <p className="text-sm font-semibold text-gray-900">Notificaciones recientes</p>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="max-h-72 overflow-y-auto divide-y divide-gray-50">
        {loading && (
          <p className="text-xs text-gray-400 text-center py-6">Cargando...</p>
        )}
        {!loading && contracts.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-6">
            Sin contratos nuevos en las últimas 48 horas.
          </p>
        )}
        {contracts.map((c) => (
          <a
            key={c.id}
            href={`/contracts/${c.id}`}
            className="block px-4 py-3 hover:bg-gray-50 transition"
            onClick={onClose}
          >
            <p className="text-sm font-medium text-gray-900 line-clamp-1">{c.title}</p>
            <div className="flex items-center justify-between mt-1">
              <span className="text-xs text-gray-400">{c.source}</span>
              <span className="text-xs font-semibold text-brand-600">{money(c.amount)}</span>
            </div>
            {c.deadline && (
              <p className="text-xs text-gray-400 mt-0.5">Cierra: {date(c.deadline)}</p>
            )}
          </a>
        ))}
      </div>
      {contracts.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-100">
          <a href="/contracts" className="text-xs text-brand-600 hover:underline font-medium">
            Ver todos los contratos →
          </a>
        </div>
      )}
    </div>
  );
}

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const [showNotifs, setShowNotifs] = useState(false);
  const { user, logout } = useAuth();

  return (
    <header className="lg:hidden sticky top-0 z-30 bg-white border-b border-gray-200">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <button onClick={() => setOpen(!open)} className="p-1 rounded-lg hover:bg-gray-100">
            {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
          <span className="font-bold text-gray-900">Jobper</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <button
              onClick={() => setShowNotifs((v) => !v)}
              className="p-2 rounded-lg hover:bg-gray-100"
              title="Notificaciones"
            >
              <Bell className="h-5 w-5 text-gray-500" />
            </button>
            {showNotifs && <NotificationPanel onClose={() => setShowNotifs(false)} />}
          </div>
          <button onClick={logout} className="p-2 rounded-lg hover:bg-gray-100">
            <LogOut className="h-5 w-5 text-gray-500" />
          </button>
        </div>
      </div>

      {open && (
        <nav className="px-4 pb-4 space-y-1">
          {[
            ["/dashboard", "Dashboard"],
            ["/contracts", "Contratos"],
            ["/favorites", "Favoritos"],
            ["/pipeline", "Pipeline"],
            ["/marketplace", "Marketplace"],
            ["/payments", "Plan"],
            ["/support", "Soporte"],
            ["/settings", "Configuración"],
          ].map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-lg text-sm font-medium ${isActive ? "bg-brand-50 text-brand-700" : "text-gray-600"}`
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
