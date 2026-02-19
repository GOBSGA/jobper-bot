import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Menu, X, Bell, LogOut } from "lucide-react";

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

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
          <button onClick={() => navigate("/support")} className="p-2 rounded-lg hover:bg-gray-100" title="Soporte">
            <Bell className="h-5 w-5 text-gray-500" />
          </button>
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
