import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { api } from "../../lib/api";
import { useToast } from "../../components/ui/Toast";
import Card, { CardHeader } from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Modal from "../../components/ui/Modal";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import { money, date } from "../../lib/format";
import { GitBranch, ChevronRight } from "lucide-react";
import { useGate } from "../../hooks/useGate";
import UpgradePrompt from "../../components/ui/UpgradePrompt";

const STAGES = [
  { key: "lead", label: "Lead", color: "gray" },
  { key: "proposal", label: "Propuesta", color: "blue" },
  { key: "submitted", label: "Enviado", color: "yellow" },
  { key: "won", label: "Ganado", color: "green" },
  { key: "lost", label: "Perdido", color: "red" },
];

export default function Pipeline() {
  const { allowed, requiredPlan } = useGate("pipeline");
  const { data, loading, refetch } = useApi("/pipeline");
  const toast = useToast();
  const [noteModal, setNoteModal] = useState(null);
  const [noteText, setNoteText] = useState("");

  const handleMove = async (entryId, stage) => {
    try {
      await api.put(`/pipeline/${entryId}/stage`, { stage });
      refetch();
    } catch (err) {
      toast.error(err.error || "Error al mover entrada");
    }
  };

  const handleNote = async () => {
    if (!noteText.trim()) return;
    try {
      await api.post(`/pipeline/${noteModal}/note`, { text: noteText });
      setNoteModal(null);
      setNoteText("");
      refetch();
    } catch (err) {
      toast.error(err.error || "Error al guardar nota");
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;

  const pipeline = data?.stages || {};
  const isEmpty = STAGES.every((s) => !(pipeline[s.key]?.length));

  if (!allowed) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Pipeline CRM</h1>
        <UpgradePrompt feature="pipeline" requiredPlan={requiredPlan}>
          <EmptyState icon={GitBranch} title="Pipeline de ventas" description="Organiza tus oportunidades de contratos en etapas: Lead → Propuesta → Enviado → Ganado." />
        </UpgradePrompt>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Pipeline CRM</h1>

      {isEmpty ? (
        <EmptyState icon={GitBranch} title="Pipeline vacío" description="Agrega contratos al pipeline desde la búsqueda o detalle." />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          {STAGES.map((stage) => (
            <div key={stage.key} className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge color={stage.color}>{stage.label}</Badge>
                <span className="text-xs text-gray-400">{pipeline[stage.key]?.length || 0}</span>
              </div>
              {(pipeline[stage.key] || []).map((entry) => (
                <Card key={entry.id} className="!p-4 space-y-2">
                  <p className="text-sm font-medium text-gray-900 line-clamp-2">{entry.contract_title || `Contrato #${entry.contract_id}`}</p>
                  {entry.value && <p className="text-xs font-semibold text-green-600">{money(entry.value)}</p>}
                  <div className="flex flex-wrap gap-1">
                    {STAGES.filter((s) => s.key !== stage.key).map((s) => (
                      <button
                        key={s.key}
                        onClick={() => handleMove(entry.id, s.key)}
                        className="text-xs px-2 py-0.5 rounded bg-gray-100 hover:bg-gray-200 text-gray-600"
                      >
                        <ChevronRight className="h-3 w-3 inline" /> {s.label}
                      </button>
                    ))}
                  </div>
                  <button onClick={() => setNoteModal(entry.id)} className="text-xs text-brand-600 hover:underline">
                    + Nota
                  </button>
                </Card>
              ))}
            </div>
          ))}
        </div>
      )}

      <Modal open={!!noteModal} onClose={() => setNoteModal(null)} title="Agregar nota">
        <textarea
          className="w-full rounded-lg border border-gray-300 p-3 text-sm"
          rows={3}
          value={noteText}
          onChange={(e) => setNoteText(e.target.value)}
          placeholder="Escribe una nota..."
        />
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setNoteModal(null)}>Cancelar</Button>
          <Button onClick={handleNote}>Guardar</Button>
        </div>
      </Modal>
    </div>
  );
}
