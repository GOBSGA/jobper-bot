import { Link } from "react-router-dom";
import { useApi } from "../../hooks/useApi";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import { money, relative } from "../../lib/format";
import { Heart } from "lucide-react";
import { useGate } from "../../hooks/useGate";

export default function Favorites() {
  const { allowed: unlimitedFavs } = useGate("favorites");
  const { data, loading } = useApi("/contracts/favorites");

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;

  const count = data?.contracts?.length || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Favoritos</h1>
        {!unlimitedFavs && <span className="text-sm text-gray-500">{count}/5 en plan Free</span>}
      </div>
      {!unlimitedFavs && count >= 5 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-center justify-between">
          <p className="text-sm text-yellow-800">Llegaste al límite de 5 favoritos en el plan Free.</p>
          <Link to="/pricing" className="text-sm font-medium text-brand-600 hover:underline whitespace-nowrap ml-3">Actualizar plan</Link>
        </div>
      )}
      {!data?.contracts?.length ? (
        <EmptyState icon={Heart} title="Sin favoritos" description="Guarda contratos que te interesen desde la búsqueda." />
      ) : (
        <div className="space-y-3">
          {data.contracts.map((c) => (
            <Link to={`/contracts/${c.id}`} key={c.id}>
              <Card className="hover:shadow-md transition">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold text-gray-900">{c.title}</h3>
                    <p className="text-xs text-gray-500 mt-1">{c.entity} · {c.source}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    {c.amount && <p className="text-sm font-bold">{money(c.amount)}</p>}
                    {c.deadline && <Badge color="blue">{relative(c.deadline)}</Badge>}
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
