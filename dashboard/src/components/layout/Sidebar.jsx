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
  UsersThree,
  CreditCard,
  ChatCircle,
  GearSix,
  ShieldCheck,
  ClipboardText,
  SignOut,
  Lightning,
} from "@phosphor-icons/react";

// Navigation grouped by purpose
const NAV_GROUPS = [
  {
    label: null, // No label for main group
    items: [
      { to: "/dashboard",   icon: SquaresFour,    label: "Dashboard" },
      { to: "/contracts",   icon: MagnifyingGlass, label: "Contratos" },
      { to: "/favorites",   icon: BookmarkSimple,  label: "Favoritos" },
    ],
  },
  {
    label: "Negocio",
    items: [
      { to: "/pipeline",    icon: Kanban,      label: "Pipeline CRM" },
      { to: "/team",        icon: UsersThree,  label: "Equipo" },
      { to: "/marketplace", icon: Storefront,  label: "Marketplace" },
      { to: "/referrals",   icon: Users,       label: "Referidos" },
    ],
  },
  {
    label: "Cuenta",
    items: [
      { to: "/payments",  icon: CreditCard, label: "Plan" },
      { to: "/support",   icon: ChatCircle, label: "Soporte" },
      { to: "/settings",  icon: GearSix,    label: "Configuración" },
    ],
  },
];

const PLAN_LABELS = {
  free: "Observador", trial: "Trial",
  cazador: "Cazador", competidor: "Competidor",
  estratega: "Estratega", dominador: "Dominador",
};

export default function Sidebar() {
  const { user, logout } = useAuth();
  const plan = user?.plan || "free";
  const showUpgrade = ["free", "trial", "expired"].includes(plan);

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-60 bg-white border-r border-surface-border h-screen sticky top-0 overflow-y-auto">
      {/* Wordmark */}
      <div className="flex items-center gap-2.5 px-5 pt-5 pb-4">
        <Logo size={28} />
        <span className="text-sm font-bold tracking-tighter text-ink-900">Jobper</span>
      </div>

      {/* Navigation groups */}
      <nav className="flex-1 px-3 space-y-4">
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi}>
            {group.label && (
              <p className="px-3 mb-1 text-[10px] font-semibold tracking-widest text-ink-400 uppercase">
                {group.label}
              </p>
            )}
            <div className="space-y-px">
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `group relative flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors duration-100 ${
                      isActive
                        ? "bg-surface-hover text-ink-900"
                        : "text-ink-400 hover:text-ink-700 hover:bg-surface-hover/60"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {/* Left indicator bar */}
                      {isActive && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] bg-brand-500 rounded-r-full" />
                      )}
                      {/* Icon container */}
                      <span className={`flex items-center justify-center w-7 h-7 rounded-lg transition-colors ${
                        isActive
                          ? "bg-brand-50 text-brand-600"
                          : "text-ink-400 group-hover:text-ink-600"
                      }`}>
                        <item.icon
                          size={16}
                          weight={isActive ? "duotone" : "regular"}
                        />
                      </span>
                      <span className={isActive ? "text-ink-900 font-semibold" : ""}>
                        {item.label}
                      </span>
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}

        {/* Admin section */}
        {user?.is_admin && (
          <div>
            <p className="px-3 mb-1 text-[10px] font-semibold tracking-widest text-ink-400 uppercase">
              Admin
            </p>
            <div className="space-y-px">
              {[
                { to: "/admin",          icon: ShieldCheck,   label: "Dashboard" },
                { to: "/admin/payments", icon: ClipboardText, label: "Revisar Pagos" },
                { to: "/admin/users",    icon: Users,         label: "Usuarios" },
              ].map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `group relative flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-surface-hover text-ink-900"
                        : "text-ink-400 hover:text-ink-700 hover:bg-surface-hover/60"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] bg-brand-500 rounded-r-full" />
                      )}
                      <span className={`flex items-center justify-center w-7 h-7 rounded-lg ${
                        isActive ? "bg-brand-50 text-brand-600" : "text-ink-400"
                      }`}>
                        <item.icon size={16} weight={isActive ? "duotone" : "regular"} />
                      </span>
                      <span className={isActive ? "font-semibold text-ink-900" : ""}>{item.label}</span>
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        )}
      </nav>

      {/* Upgrade CTA */}
      {showUpgrade && (
        <div className="px-3 pb-3 pt-2">
          <Link
            to="/payments"
            className="flex items-center justify-between px-3 py-2.5 bg-brand-500 text-white rounded-xl text-xs font-semibold hover:bg-brand-600 transition-colors group"
          >
            <div className="flex items-center gap-2">
              <Lightning size={14} weight="fill" className="text-yellow-300" />
              <span>Desbloquear todo</span>
            </div>
            <span className="opacity-60 group-hover:opacity-100 transition-opacity text-[10px]">→</span>
          </Link>
        </div>
      )}

      {/* Divider */}
      <div className="mx-4 h-px bg-surface-border" />

      {/* User footer */}
      <div className="px-4 py-4">
        <div className="flex items-center gap-2.5">
          <UserAvatar email={user?.email} size="md" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-ink-900 truncate leading-tight">
              {user?.company_name || user?.email}
            </p>
            <p className="text-[10px] text-ink-400 capitalize mt-px leading-tight">
              {PLAN_LABELS[plan] || plan}
            </p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg hover:bg-surface-hover transition-colors"
            title="Cerrar sesión"
          >
            <SignOut size={14} className="text-ink-400" />
          </button>
        </div>
      </div>
    </aside>
  );
}
