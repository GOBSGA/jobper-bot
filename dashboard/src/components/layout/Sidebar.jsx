import { NavLink, Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import Logo from "../ui/Logo";
import UserAvatar from "../ui/UserAvatar";
import { getPlanColor } from "../../lib/planConfig";
import {
  SquaresFour,
  MagnifyingGlass,
  BookmarkSimple,
  Kanban,
  Storefront,
  Users,
  CreditCard,
  ChatCircle,
  GearSix,
  ShieldCheck,
  ClipboardText,
  SignOut,
  ArrowRight,
} from "@phosphor-icons/react";

const nav = [
  { to: "/dashboard",   icon: SquaresFour,    label: "Dashboard" },
  { to: "/contracts",   icon: MagnifyingGlass, label: "Contratos" },
  { to: "/favorites",   icon: BookmarkSimple,  label: "Favoritos" },
  { to: "/pipeline",    icon: Kanban,          label: "Pipeline CRM" },
  { to: "/marketplace", icon: Storefront,      label: "Marketplace" },
  { to: "/referrals",   icon: Users,           label: "Referidos" },
  { to: "/payments",    icon: CreditCard,      label: "Plan" },
  { to: "/support",     icon: ChatCircle,      label: "Soporte" },
  { to: "/settings",    icon: GearSix,         label: "Configuración" },
];

const FREE_PLANS = ["free", "trial", "expired"];

const PLAN_LABELS = {
  free:        "Observador",
  trial:       "Trial",
  cazador:     "Cazador",
  competidor:  "Competidor",
  estratega:   "Estratega",
  dominador:   "Dominador",
};

export default function Sidebar() {
  const { user, logout } = useAuth();
  const plan = user?.plan || "free";
  const showUpgrade = FREE_PLANS.includes(plan);

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-60 bg-white border-r border-surface-border h-screen sticky top-0">
      {/* Wordmark */}
      <div className="flex items-center gap-2.5 px-5 py-5">
        <Logo size={30} />
        <span className="text-sm font-bold tracking-tighter text-ink-900">Jobper</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-px">
        {nav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-colors duration-100 ${
                isActive
                  ? "bg-brand-50 text-brand-600"
                  : "text-ink-600 hover:text-ink-900 hover:bg-surface-hover"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon
                  size={17}
                  weight={isActive ? "duotone" : "regular"}
                  className="flex-shrink-0"
                />
                {item.label}
              </>
            )}
          </NavLink>
        ))}

        {user?.is_admin && (
          <>
            <div className="pt-4 pb-1 px-3">
              <p className="text-2xs font-semibold text-ink-400 uppercase tracking-wider">Admin</p>
            </div>
            {[
              { to: "/admin",          icon: ShieldCheck,   label: "Dashboard" },
              { to: "/admin/payments", icon: ClipboardText, label: "Revisar Pagos" },
              { to: "/admin/users",    icon: Users,         label: "Usuarios" },
            ].map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-brand-50 text-brand-600"
                      : "text-ink-600 hover:text-ink-900 hover:bg-surface-hover"
                  }`
                }
              >
                <item.icon size={17} weight="regular" className="flex-shrink-0" />
                {item.label}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      {/* Upgrade CTA — flat, not gradient */}
      {showUpgrade && (
        <div className="px-3 pb-3">
          <Link
            to="/payments"
            className="flex items-center justify-between px-4 py-3 bg-ink-900 text-white rounded-xl text-xs font-medium hover:bg-ink-600 transition-colors group"
          >
            <span>Desbloquear todo</span>
            <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      )}

      {/* User footer */}
      <div className="border-t border-surface-border px-4 py-4">
        <div className="flex items-center gap-2.5">
          <UserAvatar email={user?.email} size="md" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-ink-900 truncate">
              {user?.company_name || user?.email}
            </p>
            <p className="text-2xs text-ink-400 capitalize mt-px">
              {PLAN_LABELS[plan] || plan}
            </p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg hover:bg-surface-hover transition-colors"
            title="Cerrar sesión"
          >
            <SignOut size={15} className="text-ink-400" />
          </button>
        </div>
      </div>
    </aside>
  );
}
