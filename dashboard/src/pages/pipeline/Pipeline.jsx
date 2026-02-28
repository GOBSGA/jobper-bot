import { useState, useEffect, useCallback } from "react";
import { useApi } from "../../hooks/useApi";
import { api } from "../../lib/api";
import { useToast } from "../../components/ui/Toast";
import Card, { CardHeader } from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Modal from "../../components/ui/Modal";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import UserAvatar from "../../components/ui/UserAvatar";
import { money, date } from "../../lib/format";
import { GitBranch, ChevronRight } from "lucide-react";
import { ChatCircle, X } from "@phosphor-icons/react";
import { useGate } from "../../hooks/useGate";
import UpgradePrompt from "../../components/ui/UpgradePrompt";

const STAGES = [
  { key: "lead", label: "Lead", color: "gray" },
  { key: "proposal", label: "Propuesta", color: "blue" },
  { key: "submitted", label: "Enviado", color: "yellow" },
  { key: "won", label: "Ganado", color: "green" },
  { key: "lost", label: "Perdido", color: "red" },
];

function CommentPanel({ entry, teamMembers, onClose }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [sending, setSending] = useState(false);
  const toast = useToast();

  const fetchComments = useCallback(async () => {
    try {
      const res = await api.get(`/pipeline/${entry.id}/comments`);
      setComments(res.comments || []);
    } catch {
      // silent polling
    }
  }, [entry.id]);

  useEffect(() => {
    fetchComments();
    const interval = setInterval(fetchComments, 5000);
    return () => clearInterval(interval);
  }, [fetchComments]);

  const sendComment = async () => {
    if (!newComment.trim()) return;
    setSending(true);
    try {
      await api.post(`/pipeline/${entry.id}/comments`, { content: newComment });
      setNewComment("");
      fetchComments();
    } catch (err) {
      toast.error(err.error || "Error al enviar comentario");
    } finally {
      setSending(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) sendComment();
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 flex-shrink-0">
        <div>
          <p className="text-xs font-semibold text-gray-900 line-clamp-1">
            {entry.contract_title || `Contrato #${entry.contract_id}`}
          </p>
          <p className="text-[10px] text-gray-400">Comentarios</p>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-400"
        >
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4 min-h-0">
        {comments.length === 0 ? (
          <p className="text-xs text-gray-400 text-center pt-6">Sin comentarios aún.</p>
        ) : (
          comments.map((c) => (
            <div key={c.id} className="space-y-1">
              <div className="flex items-center gap-1.5">
                <UserAvatar email={c.user_email} size="sm" />
                <span className="text-xs font-medium text-gray-700">{c.user_email}</span>
                <span className="text-[10px] text-gray-400 ml-auto">{date(c.created_at)}</span>
              </div>
              <p className="text-sm text-gray-900 pl-9">{c.content}</p>
            </div>
          ))
        )}
      </div>

      <div className="px-4 py-3 border-t border-gray-100 flex-shrink-0">
        <div className="flex gap-2">
          <textarea
            className="flex-1 rounded-xl border border-gray-200 p-2.5 text-sm resize-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 outline-none"
            rows={2}
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Escribe un comentario... (⌘+Enter)"
          />
          <Button onClick={sendComment} disabled={sending || !newComment.trim()} className="self-end">
            {sending ? <Spinner className="h-4 w-4" /> : "Enviar"}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function Pipeline() {
  const { allowed, requiredPlan } = useGate("pipeline");
  const { data, loading, refetch } = useApi("/pipeline");
  const { data: teamData } = useApi("/team", { immediate: true });
  const toast = useToast();
  const [noteModal, setNoteModal] = useState(null);
  const [noteText, setNoteText] = useState("");
  const [moving, setMoving] = useState(null);
  const [commentEntry, setCommentEntry] = useState(null);
  const [assigning, setAssigning] = useState(null);

  const teamMembers = (teamData?.members || []).filter((m) => m.accepted_at);
  const hasTeam = teamMembers.length > 0;

  const handleMove = async (entryId, stage) => {
    if (moving) return;
    setMoving(entryId);
    try {
      await api.put(`/pipeline/${entryId}/stage`, { stage });
      refetch();
    } catch (err) {
      toast.error(err.error || "Error al mover entrada");
    } finally {
      setMoving(null);
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

  const handleAssign = async (entryId, userId) => {
    try {
      await api.put(`/pipeline/${entryId}/assign`, { user_id: userId || null });
      setAssigning(null);
      refetch();
    } catch (err) {
      toast.error(err.error || "Error al asignar");
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
        <div className="flex gap-4">
          {/* Board */}
          <div className={`flex-1 overflow-x-auto ${commentEntry ? "lg:max-w-[calc(100%-320px)]" : ""}`}>
            <div className="flex gap-3 min-w-max pb-2">
              {STAGES.map((stage) => (
                <div key={stage.key} className="w-52 space-y-2 flex-shrink-0">
                  <div className="flex items-center gap-2">
                    <Badge color={stage.color}>{stage.label}</Badge>
                    <span className="text-xs text-gray-400">{pipeline[stage.key]?.length || 0}</span>
                  </div>
                  {(pipeline[stage.key] || []).map((entry) => {
                    const assignee = entry.assigned_to && hasTeam
                      ? teamMembers.find((m) => m.member_user_id === entry.assigned_to)
                      : null;

                    return (
                      <Card key={entry.id} className="!p-4 space-y-2">
                        <p className="text-sm font-medium text-gray-900 line-clamp-2">
                          {entry.contract_title || `Contrato #${entry.contract_id}`}
                        </p>
                        {entry.value && (
                          <p className="text-xs font-semibold text-green-600">{money(entry.value)}</p>
                        )}

                        {/* Assignment + comments row */}
                        <div className="flex items-center gap-1 flex-wrap">
                          {hasTeam && (
                            assignee ? (
                              <button
                                onClick={() => setAssigning(assigning === entry.id ? null : entry.id)}
                                className="flex items-center gap-1 text-[10px] bg-blue-50 text-blue-700 rounded-lg px-1.5 py-0.5 hover:bg-blue-100 transition-colors"
                              >
                                <UserAvatar email={assignee.email} size="sm" />
                                <span className="truncate max-w-[70px]">{assignee.email.split("@")[0]}</span>
                              </button>
                            ) : (
                              <button
                                onClick={() => setAssigning(assigning === entry.id ? null : entry.id)}
                                className="text-[10px] text-gray-400 hover:text-gray-600 transition-colors"
                              >
                                + Asignar
                              </button>
                            )
                          )}

                          <button
                            onClick={() => setCommentEntry(commentEntry?.id === entry.id ? null : entry)}
                            className={`ml-auto flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-lg transition-colors ${
                              commentEntry?.id === entry.id
                                ? "bg-blue-100 text-blue-700"
                                : "text-gray-400 hover:text-gray-600"
                            }`}
                          >
                            <ChatCircle size={12} />
                            {entry.comments_count > 0 && <span>{entry.comments_count}</span>}
                          </button>
                        </div>

                        {/* Assignment dropdown */}
                        {assigning === entry.id && hasTeam && (
                          <div className="border border-gray-200 rounded-lg bg-white shadow-sm text-xs overflow-hidden">
                            <button
                              onClick={() => handleAssign(entry.id, null)}
                              className="w-full text-left px-2 py-1.5 hover:bg-gray-50 text-gray-400"
                            >
                              Sin asignar
                            </button>
                            {teamMembers.map((m) => (
                              <button
                                key={m.id}
                                onClick={() => handleAssign(entry.id, m.member_user_id)}
                                className="w-full text-left px-2 py-1.5 hover:bg-gray-50 flex items-center gap-1.5"
                              >
                                <UserAvatar email={m.email} size="sm" />
                                {m.email}
                              </button>
                            ))}
                          </div>
                        )}

                        {/* Stage buttons */}
                        <div className="flex flex-wrap gap-1">
                          {STAGES.filter((s) => s.key !== stage.key).map((s) => (
                            <button
                              key={s.key}
                              onClick={() => handleMove(entry.id, s.key)}
                              disabled={!!moving}
                              className="text-xs px-2 py-0.5 rounded bg-gray-100 hover:bg-gray-200 text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <ChevronRight className="h-3 w-3 inline" /> {s.label}
                            </button>
                          ))}
                        </div>

                        <button onClick={() => setNoteModal(entry.id)} className="text-xs text-blue-600 hover:underline">
                          + Nota
                        </button>
                      </Card>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          {/* Comment panel */}
          {commentEntry && (
            <div className="w-80 flex-shrink-0 bg-white rounded-2xl border border-gray-200 flex flex-col overflow-hidden" style={{ height: "calc(100vh - 160px)", position: "sticky", top: 16 }}>
              <CommentPanel
                entry={commentEntry}
                teamMembers={teamMembers}
                onClose={() => setCommentEntry(null)}
              />
            </div>
          )}
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
