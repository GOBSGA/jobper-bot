import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApi } from "../../hooks/useApi";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Spinner from "../../components/ui/Spinner";
import { date } from "../../lib/format";
import { getBadgeColor } from "../../lib/planConfig";
import { Users, MagnifyingGlass, CaretLeft, CaretRight } from "@phosphor-icons/react";

export default function AdminUsers() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const { data, loading } = useApi(
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
    <div className="space-y-5 pb-8">
      <div className="flex items-center gap-2">
        <Users size={22} className="text-brand-600" weight="duotone" />
        <h1 className="text-xl sm:text-2xl font-bold text-ink-900">Usuarios ({total})</h1>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <Input
          className="flex-1"
          placeholder="Buscar por email o empresa..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <Button type="submit">
          <MagnifyingGlass size={15} /> Buscar
        </Button>
        {search && (
          <Button
            variant="secondary"
            onClick={() => {
              setSearch("");
              setSearchInput("");
              setPage(1);
            }}
          >
            Limpiar
          </Button>
        )}
      </form>

      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      ) : (
        <>
          <Card className="overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-surface-border bg-surface-hover">
                    <th className="text-left px-4 py-3 text-xs font-semibold text-ink-400 uppercase">
                      ID
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-ink-400 uppercase">
                      Email
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-ink-400 uppercase hidden sm:table-cell">
                      Empresa
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-ink-400 uppercase">
                      Plan
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-ink-400 uppercase hidden lg:table-cell">
                      Sector
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-ink-400 uppercase hidden md:table-cell">
                      Confianza
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-ink-400 uppercase hidden sm:table-cell">
                      Registro
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr
                      key={u.id}
                      className="border-b border-surface-border hover:bg-surface-hover transition cursor-pointer last:border-0"
                      onClick={() => navigate(`/admin/users/${u.id}`)}
                    >
                      <td className="px-4 py-3 text-ink-400 font-mono text-xs">#{u.id}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="h-7 w-7 rounded-full bg-gradient-to-br from-brand-400 to-purple-400 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                            {u.email?.[0]?.toUpperCase()}
                          </div>
                          <span className="font-medium text-ink-900 truncate max-w-[160px] sm:max-w-[200px]">
                            {u.email}
                          </span>
                          {u.is_admin && (
                            <Badge color="red" className="hidden sm:inline-flex">
                              admin
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-ink-600 truncate max-w-[140px] hidden sm:table-cell">
                        {u.company_name || "—"}
                      </td>
                      <td className="px-4 py-3">
                        <Badge color={getBadgeColor(u.plan) || "gray"}>{u.plan || "free"}</Badge>
                      </td>
                      <td className="px-4 py-3 text-ink-400 text-xs hidden lg:table-cell">
                        {u.sector || "—"}
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        <span className="text-xs text-ink-400">{u.trust_level || "new"}</span>
                        {u.verified_payments_count > 0 && (
                          <span className="text-xs text-accent-600 ml-1">
                            ({u.verified_payments_count}✓)
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-ink-400 hidden sm:table-cell">
                        {date(u.created_at)}
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-sm text-ink-400">
                        Sin usuarios
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          {pages > 1 && (
            <div className="flex items-center justify-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <CaretLeft size={14} />
              </Button>
              <span className="text-sm text-ink-400">
                Página {page} de {pages}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= pages}
                onClick={() => setPage((p) => p + 1)}
              >
                <CaretRight size={14} />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
