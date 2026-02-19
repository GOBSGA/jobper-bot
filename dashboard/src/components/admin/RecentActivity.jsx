import { Link } from "react-router-dom";
import Card, { CardHeader } from "../ui/Card";
import Badge from "../ui/Badge";
import { money, relative } from "../../lib/format";
import { getBadgeColor } from "../../lib/planConfig";
import { ChevronRight, CheckCircle, XCircle, Clock } from "lucide-react";

const STATUS_COLORS = {
  approved: "green",
  pending: "gray",
  review: "yellow",
  grace: "blue",
  rejected: "red",
};

/**
 * Recent activity - Signups and Payments
 */
export default function RecentActivity({ kpis }) {
  const k = kpis || {};

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Recent signups */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <CardHeader title="Registros recientes" />
          <Link
            to="/admin/users"
            className="text-xs text-brand-600 hover:text-brand-700 flex items-center gap-1"
          >
            Ver todos <ChevronRight className="h-3 w-3" />
          </Link>
        </div>
        <div className="space-y-2">
          {(k.recent_signups || []).length === 0 && (
            <p className="text-sm text-gray-400">Sin registros aún</p>
          )}
          {(k.recent_signups || []).map((u) => (
            <div
              key={u.id}
              className="flex items-center gap-3 py-1.5 border-b border-gray-50 last:border-0"
            >
              <div className="h-7 w-7 rounded-full bg-gradient-to-br from-brand-400 to-purple-400 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                {u.email?.[0]?.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {u.company_name || u.email}
                </p>
                <p className="text-xs text-gray-400 truncate">{u.email}</p>
              </div>
              <div className="flex flex-col items-end gap-1">
                <Badge color={getBadgeColor(u.plan) || "gray"}>{u.plan || "free"}</Badge>
                <span className="text-[10px] text-gray-400">{relative(u.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Recent payments */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <CardHeader title="Pagos recientes" />
          <Link
            to="/admin/payments"
            className="text-xs text-brand-600 hover:text-brand-700 flex items-center gap-1"
          >
            Revisar <ChevronRight className="h-3 w-3" />
          </Link>
        </div>
        <div className="space-y-2">
          {(k.recent_payments || []).length === 0 && (
            <p className="text-sm text-gray-400">Sin pagos aún</p>
          )}
          {(k.recent_payments || []).map((p) => (
            <div
              key={p.id}
              className="flex items-center gap-3 py-1.5 border-b border-gray-50 last:border-0"
            >
              <div
                className={`h-7 w-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                  p.status === "approved"
                    ? "bg-green-100"
                    : p.status === "rejected"
                      ? "bg-red-100"
                      : p.status === "grace"
                        ? "bg-blue-100"
                        : "bg-yellow-100"
                }`}
              >
                {p.status === "approved" ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : p.status === "rejected" ? (
                  <XCircle className="h-4 w-4 text-red-600" />
                ) : (
                  <Clock className="h-4 w-4 text-yellow-600" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{p.user_email}</p>
                <p className="text-xs text-gray-400">
                  {p.plan || "—"} · {p.reference ? `#${p.reference.slice(-6)}` : "—"}
                </p>
              </div>
              <div className="flex flex-col items-end gap-1">
                <span className="text-sm font-bold text-gray-900">{money(p.amount)}</span>
                <Badge color={STATUS_COLORS[p.status] || "gray"}>{p.status}</Badge>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
