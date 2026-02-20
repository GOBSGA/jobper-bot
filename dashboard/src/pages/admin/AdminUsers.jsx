import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Spinner from "../../components/ui/Spinner";
import { date } from "../../lib/format";
import { getBadgeColor } from "../../lib/planConfig";
import { Users, Search, ChevronLeft, ChevronRight } from "lucide-react";

export default function AdminUsers() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const { data, loading, refetch } = useApi(
    `/admin/users?page=${page}&per_page=25${search ? `&search=${encodeURIComponent(search)}` : ""}`
  );

  const handleSearch = (e) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const users = data?.results || [];
  const total = data?.total || 0;
  const pages = Math.ceil(total / 25);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Users className="h-6 w-6 text-brand-600" />
        <h1 className="text-2xl font-bold text-gray-900">Usuarios ({total})</h1>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <Input
          className="flex-1"
          placeholder="Buscar por email o empresa..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <Button type="submit"><Search className="h-4 w-4" /> Buscar</Button>
        {search && (
          <Button variant="secondary" onClick={() => { setSearch(""); setSearchInput(""); setPage(1); }}>
            Limpiar
          </Button>
        )}
      </form>

      {loading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <>
          <Card className="overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">ID</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Email</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Empresa</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Plan</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Sector</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Confianza</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Registro</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50 transition">
                    <td className="px-4 py-3 text-gray-400 font-mono text-xs">#{u.id}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded-full bg-gradient-to-br from-brand-400 to-purple-400 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                          {u.email?.[0]?.toUpperCase()}
                        </div>
                        <span className="font-medium text-gray-800 truncate max-w-[180px]">{u.email}</span>
                        {u.is_admin && <Badge color="red">admin</Badge>}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600 truncate max-w-[140px]">{u.company_name || "—"}</td>
                    <td className="px-4 py-3">
                      <Badge color={getBadgeColor(u.plan) || "gray"}>{u.plan || "free"}</Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{u.sector || "—"}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-gray-500">{u.trust_level || "new"}</span>
                      {u.verified_payments_count > 0 && (
                        <span className="text-xs text-green-600 ml-1">({u.verified_payments_count}✓)</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">{date(u.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {pages > 1 && (
            <div className="flex items-center justify-center gap-3">
              <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-gray-500">Página {page} de {pages}</span>
              <Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => setPage(p => p + 1)}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
