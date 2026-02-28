import { NavLink } from "react-router-dom";
import { useApi } from "../../hooks/useApi";
import {
  SquaresFour,
  MagnifyingGlass,
  Kanban,
  Storefront,
  DotsThree,
} from "@phosphor-icons/react";
import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import Logo from "../ui/Logo";
import {
  BookmarkSimple, Users, UsersThree, CreditCard, ChatCircle, GearSix, SignOut,
} from "@phosphor-icons/react";

const PRIMARY = [
  { to: "/dashboard",   icon: SquaresFour,    label: "Inicio" },
  { to: "/contracts",   icon: MagnifyingGlass, label: "Contratos" },
  { to: "/pipeline",    icon: Kanban,          label: "Pipeline" },
  { to: "/marketplace", icon: Storefront,      label: "Mercado" },
];

const MORE_NAV = [
  { to: "/favorites",  icon: BookmarkSimple, label: "Favoritos" },
  { to: "/team",       icon: UsersThree,     label: "Equipo" },
  { to: "/referrals",  icon: Users,          label: "Referidos" },
  { to: "/payments",   icon: CreditCard,     label: "Plan" },
  { to: "/support",    icon: ChatCircle,     label: "Soporte" },
  { to: "/settings",   icon: GearSix,        label: "Configuración" },
];

function MoreSheet({ onClose }) {
  const { user, logout } = useAuth();
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-ink-900/20 backdrop-blur-[2px]"
        onClick={onClose}
      />
      {/* Bottom sheet */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-white rounded-t-3xl border-t border-surface-border shadow-md animate-slide-up">
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 rounded-full bg-surface-border" />
        </div>

        {/* User info */}
        <div className="flex items-center gap-3 px-5 py-3 border-b border-surface-border">
          <div className="w-9 h-9 rounded-xl bg-ink-900 text-white flex items-center justify-center text-sm font-bold">
            {(user?.company_name || user?.email || "?")[0].toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-ink-900 truncate">
              {user?.company_name || user?.email}
            </p>
            <p className="text-2xs text-ink-400 capitalize">{user?.plan || "free"}</p>
          </div>
          <button onClick={() => { logout(); onClose(); }} className="p-2 rounded-xl hover:bg-surface-hover">
            <SignOut size={16} className="text-ink-400" />
          </button>
        </div>

        {/* Nav items */}
        <div className="grid grid-cols-3 gap-1 p-4">
          {MORE_NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1.5 py-3 rounded-2xl transition-colors ${
                  isActive
                    ? "bg-brand-50 text-brand-600"
                    : "text-ink-500 hover:bg-surface-hover"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon size={22} weight={isActive ? "duotone" : "regular"} />
                  <span className="text-[10px] font-medium leading-none">{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>

        {/* Safe area spacer */}
        <div className="h-safe-b pb-2" />
      </div>
    </>
  );
}

export default function BottomNav() {
  const [showMore, setShowMore] = useState(false);
  const { data: inbox } = useApi("/marketplace/inbox");
  const unread = inbox?.total_unread || 0;

  return (
    <>
      {/* Fixed bottom bar */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-30 bg-white border-t border-surface-border">
        <div className="flex items-stretch h-16 safe-b">
          {PRIMARY.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex-1 flex flex-col items-center justify-center gap-1 transition-colors ${
                  isActive ? "text-brand-600" : "text-ink-400"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon
                    size={22}
                    weight={isActive ? "duotone" : "regular"}
                    className={item.to === "/marketplace" && unread > 0 ? "relative" : ""}
                  />
                  {item.to === "/marketplace" && unread > 0 && (
                    <span className="absolute top-3 ml-3 h-2 w-2 rounded-full bg-red-500" />
                  )}
                  <span className="text-[10px] font-medium leading-none">{item.label}</span>
                </>
              )}
            </NavLink>
          ))}

          {/* More */}
          <button
            onClick={() => setShowMore(true)}
            className="flex-1 flex flex-col items-center justify-center gap-1 text-ink-400"
          >
            <DotsThree size={22} weight="bold" />
            <span className="text-[10px] font-medium leading-none">Más</span>
          </button>
        </div>
      </nav>

      {/* More sheet */}
      {showMore && <MoreSheet onClose={() => setShowMore(false)} />}
    </>
  );
}
