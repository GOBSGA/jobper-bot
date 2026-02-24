import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { api } from "../../lib/api";
import { useToast } from "../../components/ui/Toast";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Modal from "../../components/ui/Modal";
import Input from "../../components/ui/Input";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import { money } from "../../lib/format";
import { Store, Plus, Star, Eye, Mail, Phone } from "lucide-react";
import { useGate } from "../../hooks/useGate";
import UpgradePrompt from "../../components/ui/UpgradePrompt";

export default function Marketplace() {
  const { allowed, requiredPlan } = useGate("marketplace");
  const { data, loading, refetch } = useApi("/marketplace");
  const toast = useToast();
  const [showPublish, setShowPublish] = useState(false);
  const [contactInfo, setContactInfo] = useState(null);
  const [form, setForm] = useState({ title: "", description: "", budget_min: "", category: "", contact_phone: "", city: "" });
  const [publishing, setPublishing] = useState(false);
  const [revealing, setRevealing] = useState(false);

  const publish = async (e) => {
    e.preventDefault();
    setPublishing(true);
    try {
      await api.post("/marketplace", {
        title: form.title,
        description: form.description,
        budget_min: form.budget_min ? Number(form.budget_min) : undefined,
        category: form.category || undefined,
        contact_phone: form.contact_phone || undefined,
        city: form.city || undefined,
      });
      setShowPublish(false);
      setForm({ title: "", description: "", budget_min: "", category: "", contact_phone: "", city: "" });
      toast.success("Contrato publicado exitosamente");
      refetch();
    } catch (err) {
      toast.error(err.error || "Error al publicar contrato");
    } finally {
      setPublishing(false);
    }
  };

  const reveal = async (id) => {
    if (revealing) return;
    setRevealing(true);
    try {
      const res = await api.get(`/marketplace/${id}/contact`);
      setContactInfo(res);
    } catch (err) {
      toast.error(err.error || "Error al obtener contacto");
    } finally {
      setRevealing(false);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;

  if (!allowed) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Marketplace</h1>
        <UpgradePrompt feature="marketplace" requiredPlan={requiredPlan}>
          <EmptyState icon={Store} title="Marketplace de servicios" description="Publica tus servicios y encuentra subcontratistas para tus proyectos." />
        </UpgradePrompt>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Marketplace</h1>
        <Button onClick={() => setShowPublish(true)}><Plus className="h-4 w-4" /> Publicar</Button>
      </div>

      {!data?.results?.length ? (
        <EmptyState icon={Store} title="Marketplace vacío" description="Sé el primero en publicar un contrato o servicio." action={<Button onClick={() => setShowPublish(true)}>Publicar ahora</Button>} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.results.map((c) => (
            <Card key={c.id} className="space-y-3">
              <div className="flex items-start justify-between">
                <h3 className="text-sm font-semibold text-gray-900 line-clamp-2">{c.title}</h3>
                {c.is_featured && <Star className="h-4 w-4 text-yellow-500 fill-yellow-500 flex-shrink-0" />}
              </div>
              {c.category && <p className="text-xs text-gray-500">{c.category}</p>}
              {c.budget_min && <p className="text-sm font-bold text-gray-900">{money(c.budget_min)}{c.budget_max ? ` - ${money(c.budget_max)}` : ""}</p>}
              {c.description && <p className="text-xs text-gray-600 line-clamp-3">{c.description}</p>}
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" onClick={() => reveal(c.id)} disabled={revealing}>
                  <Eye className="h-3 w-3" /> Contacto
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Contact info modal */}
      <Modal open={!!contactInfo} onClose={() => setContactInfo(null)} title="Información de contacto">
        {contactInfo && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
              <Mail className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500">Email</p>
                <p className="text-sm font-medium">{contactInfo.contact_email || "No disponible"}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
              <Phone className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500">Teléfono</p>
                <p className="text-sm font-medium">{contactInfo.contact_phone || "No disponible"}</p>
              </div>
            </div>
            <Button className="w-full" variant="secondary" onClick={() => setContactInfo(null)}>Cerrar</Button>
          </div>
        )}
      </Modal>

      {/* Publish modal */}
      <Modal open={showPublish} onClose={() => setShowPublish(false)} title="Publicar contrato">
        <form onSubmit={publish} className="space-y-4">
          <Input label="Título" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <textarea
            className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition"
            rows={3}
            placeholder="Descripción del contrato..."
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Presupuesto (COP)" type="number" value={form.budget_min} onChange={(e) => setForm({ ...form, budget_min: e.target.value })} />
            <Input label="Categoría" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} placeholder="Ej: tecnología, construcción" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Ciudad" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} placeholder="Ej: Bogotá" />
            <Input label="Teléfono" value={form.contact_phone} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" type="button" onClick={() => setShowPublish(false)}>Cancelar</Button>
            <Button type="submit" disabled={publishing}>{publishing ? "Publicando..." : "Publicar"}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
