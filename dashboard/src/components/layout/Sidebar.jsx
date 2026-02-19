import { NavLink, Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import Logo from "../ui/Logo";
import UserAvatar from "../ui/UserAvatar";
import { getPlanColor } from "../../lib/planConfig";
import {
  LayoutDashboard, Search, Heart, GitBranch, Store,
  CreditCard, Settings, Shield, MessageCircle, Users, LogOut, Zap, ClipboardCheck,
} from "lucide-react";

const nav = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/contracts", icon: Search, label: "Contratos" },
  { to: "/favorites", icon: Heart, label: "Favoritos" },
  { to: "/pipeline", icon: GitBranch, label: "Pipeline CRM" },
  { to: "/marketplace", icon: Store, label: "Marketplace" },
  { to: "/referrals", icon: Users, label: "Referidos" },
  { to: "/payments", icon: CreditCard, label: "Plan" },
  { to: "/support", icon: MessageCircle, label: "Soporte" },
  { to: "/settings", icon: Settings, label: "Configuracion" },
];

const FREE_PLANS = ["free", "trial", "expired"];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const plan = user?.plan || "free";
  const showUpgrade = FREE_PLANS.includes(plan);

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-white border-r border-gray-200/80 h-screen sticky top-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-100">
        <Logo size={34} />
        <span className="text-lg font-bold tracking-tight text-gray-900">Jobper</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
        {nav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                isActive
                  ? "bg-brand-50 text-brand-700 shadow-sm shadow-brand-100/50"
                  : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
              }`
            }
          >
            <item.icon className="h-[18px] w-[18px] flex-shrink-0" />
            {item.label}
          </NavLink>
        ))}
        {user?.is_admin && (
          <>
            <div className="pt-3 pb-1 px-3">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Admin</p>
            </div>
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-brand-50 text-brand-700 shadow-sm shadow-brand-100/50"
                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                }`
              }
            >
              <Shield className="h-[18px] w-[18px]" />
              Dashboard
            </NavLink>
            <NavLink
              to="/admin/payments"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-brand-50 text-brand-700 shadow-sm shadow-brand-100/50"
                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                }`
              }
            >
              <ClipboardCheck className="h-[18px] w-[18px]" />
              Revisar Pagos
            </NavLink>
            <NavLink
              to="/admin/users"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-brand-50 text-brand-700 shadow-sm shadow-brand-100/50"
                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                }`
              }
            >
              <Users className="h-[18px] w-[18px]" />
              Usuarios
            </NavLink>
          </>
        )}
      </nav>

      {/* Upgrade CTA */}
      {showUpgrade && (
        <div className="px-3 pb-2">
          <Link
            to="/payments"
            className="flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-brand-600 to-purple-600 text-white rounded-xl text-sm font-medium hover:from-brand-700 hover:to-purple-700 transition shadow-sm"
          >
            <Zap className="h-4 w-4" />
            <span>Desbloquear todo</span>
          </Link>
        </div>
      )}

      {/* User */}
      <div className="border-t border-gray-100 px-4 py-4">
        <div className="flex items-center gap-3">
          <UserAvatar email={user?.email} size="md" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user?.company_name || user?.email}</p>
            <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${getPlanColor(plan, "badge")}`}>
              {plan}
            </span>
          </div>
          <button onClick={logout} className="p-1.5 rounded-lg hover:bg-gray-100 transition" title="Cerrar sesion">
            <LogOut className="h-4 w-4 text-gray-400" />
          </button>
        </div>
      </div>
    </aside>
  );
}
