import { useState, useEffect, useCallback } from "react";
import { useApi } from "../../hooks/useApi";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import { useGate } from "../../hooks/useGate";
import { useToast } from "../../components/ui/Toast";
import Card, { CardHeader } from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import UpgradePrompt from "../../components/ui/UpgradePrompt";
import UserAvatar from "../../components/ui/UserAvatar";
import { money, date } from "../../lib/format";
import {
  UsersThree,
  UserPlus,
  X,
  Copy,
  CaretRight,
  ChatCircle,
  Kanban,
} from "@phosphor-icons/react";
import { GitBranch } from "lucide-react";

const STAGES = [
  { key: "lead", label: "Lead", color: "gray" },
  { key: "proposal", label: "Propuesta", color: "blue" },
  { key: "submitted", label: "Enviado", color: "yellow" },
  { key: "won", label: "Ganado", color: "green" },
  { key: "lost", label: "Perdido", color: "red" },
];

function MemberRow({ member, isOwner, onRemove }) {
  const daysSince = member.accepted_at
    ? Math.floor((Date.now() - new Date(member.accepted_at).getTime()) / 86400000)
    : null;

  return (
    <div className="flex items-center gap-3 py-2.5">
      <UserAvatar email={member.email} size="md" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-ink-900 truncate">{member.email}</p>
        <p className="text-xs text-ink-400">
          {daysSince !== null ? `Activo hace ${daysSince} días` : "Invitación enviada"}
        </p>
      </div>
      <Badge color={member.role === "admin" ? "purple" : "gray"}>
        {member.role === "admin" ? "Admin" : "Miembro"}
      </Badge>
      {isOwner && (
        <button
          onClick={() => onRemove(member.id)}
          className="p-1 rounded-lg hover:bg-red-50 text-ink-300 hover:text-red-500 transition-colors"
          title="Remover miembro"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

function PendingRow({ invite, isOwner, onCancel }) {
  const toast = useToast();
  const copyLink = () => {
    const url = `${window.location.origin}/team/accept/${invite.invite_token}`;
    navigator.clipboard.writeText(url).then(() => toast.success("Link copiado"));
  };

  return (
    <div className="flex items-center gap-3 py-2.5">
      <div className="h-8 w-8 rounded-xl bg-gray-100 flex items-center justify-center flex-shrink-0">
        <span className="text-xs font-semibold text-gray-400">{invite.email[0].toUpperCase()}</span>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-ink-900 truncate">{invite.email}</p>
        <p className="text-xs text-ink-400">Pendiente</p>
      </div>
      <button
        onClick={copyLink}
        className="p-1.5 rounded-lg hover:bg-surface-hover text-ink-300 hover:text-ink-600 transition-colors"
        title="Copiar link de invitación"
      >
        <Copy size={13} />
      </button>
      {isOwner && (
        <button
          onClick={() => onCancel(invite.id)}
          className="p-1 rounded-lg hover:bg-red-50 text-ink-300 hover:text-red-500 transition-colors"
          title="Cancelar invitación"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

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
      // silent
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
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border flex-shrink-0">
        <div>
          <p className="text-xs font-semibold text-ink-900 line-clamp-1">
            {entry.contract_title || `Contrato #${entry.contract_id}`}
          </p>
          <p className="text-[10px] text-ink-400">Comentarios del equipo</p>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-surface-hover transition-colors text-ink-400"
        >
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4 min-h-0">
        {comments.length === 0 ? (
          <p className="text-xs text-ink-400 text-center pt-6">Sin comentarios aún. Sé el primero.</p>
        ) : (
          comments.map((c) => (
            <div key={c.id} className="space-y-1">
              <div className="flex items-center gap-1.5">
                <UserAvatar email={c.user_email} size="sm" />
                <span className="text-xs font-medium text-ink-700">{c.user_email}</span>
                <span className="text-[10px] text-ink-400 ml-auto">{date(c.created_at)}</span>
              </div>
              <p className="text-sm text-ink-900 pl-9">{c.content}</p>
            </div>
          ))
        )}
      </div>

      <div className="px-4 py-3 border-t border-surface-border flex-shrink-0">
        <div className="flex gap-2">
          <textarea
            className="flex-1 rounded-xl border border-gray-200 p-2.5 text-sm resize-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400 outline-none"
            rows={2}
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Escribe un comentario... (⌘+Enter para enviar)"
          />
          <Button onClick={sendComment} disabled={sending || !newComment.trim()} className="self-end">
            {sending ? <Spinner className="h-4 w-4" /> : "Enviar"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function SharedPipeline({ ownerId, teamMembers }) {
  const { data, loading, refetch } = useApi("/team/pipeline");
  const toast = useToast();
  const [moving, setMoving] = useState(null);
  const [commentEntry, setCommentEntry] = useState(null);
  const [assigning, setAssigning] = useState(null);

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
  const allMembers = teamMembers || [];

  if (isEmpty) {
    return (
      <EmptyState
        icon={Kanban}
        title="Pipeline compartido vacío"
        description="Cuando el owner agrega contratos al pipeline, aparecerán aquí."
      />
    );
  }

  return (
    <div className="flex gap-4 h-full min-h-0">
      {/* Pipeline board */}
      <div className={`flex-1 overflow-x-auto min-h-0 ${commentEntry ? "lg:max-w-[calc(100%-320px)]" : ""}`}>
        <div className="flex gap-3 min-w-max pb-2">
          {STAGES.map((stage) => (
            <div key={stage.key} className="w-52 space-y-2 flex-shrink-0">
              <div className="flex items-center gap-2">
                <Badge color={stage.color}>{stage.label}</Badge>
                <span className="text-xs text-gray-400">{pipeline[stage.key]?.length || 0}</span>
              </div>
              {(pipeline[stage.key] || []).map((entry) => {
                const assignee = entry.assigned_to
                  ? allMembers.find((m) => m.member_user_id === entry.assigned_to)
                  : null;

                return (
                  <Card key={entry.id} className="!p-3 space-y-2">
                    <p className="text-xs font-medium text-gray-900 line-clamp-2">
                      {entry.contract_title || `Contrato #${entry.contract_id}`}
                    </p>
                    {entry.value && (
                      <p className="text-xs font-semibold text-green-600">{money(entry.value)}</p>
                    )}

                    {/* Assignee chip */}
                    <div className="flex items-center gap-1">
                      {assignee ? (
                        <button
                          onClick={() => setAssigning(assigning === entry.id ? null : entry.id)}
                          className="flex items-center gap-1 text-[10px] bg-brand-50 text-brand-700 rounded-lg px-1.5 py-0.5 hover:bg-brand-100 transition-colors"
                        >
                          <UserAvatar email={assignee.email} size="sm" />
                          <span className="truncate max-w-[80px]">{assignee.email.split("@")[0]}</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => setAssigning(assigning === entry.id ? null : entry.id)}
                          className="text-[10px] text-ink-300 hover:text-ink-600 transition-colors"
                        >
                          + Asignar
                        </button>
                      )}

                      {/* Comments button */}
                      <button
                        onClick={() => setCommentEntry(commentEntry?.id === entry.id ? null : entry)}
                        className={`ml-auto flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-lg transition-colors ${
                          commentEntry?.id === entry.id
                            ? "bg-brand-100 text-brand-700"
                            : "text-ink-300 hover:text-ink-600"
                        }`}
                      >
                        <ChatCircle size={11} />
                        {entry.comments_count > 0 && <span>{entry.comments_count}</span>}
                      </button>
                    </div>

                    {/* Assignment dropdown */}
                    {assigning === entry.id && (
                      <div className="border border-gray-200 rounded-lg bg-white shadow-sm text-xs overflow-hidden">
                        <button
                          onClick={() => handleAssign(entry.id, null)}
                          className="w-full text-left px-2 py-1.5 hover:bg-surface-hover text-ink-400"
                        >
                          Sin asignar
                        </button>
                        {allMembers
                          .filter((m) => m.accepted_at)
                          .map((m) => (
                            <button
                              key={m.id}
                              onClick={() => handleAssign(entry.id, m.member_user_id)}
                              className="w-full text-left px-2 py-1.5 hover:bg-surface-hover flex items-center gap-1.5"
                            >
                              <UserAvatar email={m.email} size="sm" />
                              {m.email}
                            </button>
                          ))}
                      </div>
                    )}

                    {/* Stage buttons */}
                    <div className="flex flex-wrap gap-1 pt-1">
                      {STAGES.filter((s) => s.key !== stage.key).map((s) => (
                        <button
                          key={s.key}
                          onClick={() => handleMove(entry.id, s.key)}
                          disabled={!!moving}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 hover:bg-gray-200 text-gray-600 disabled:opacity-50"
                        >
                          <CaretRight size={10} className="inline" /> {s.label}
                        </button>
                      ))}
                    </div>
                  </Card>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Comment panel */}
      {commentEntry && (
        <div className="w-80 flex-shrink-0 bg-white rounded-2xl border border-surface-border flex flex-col overflow-hidden">
          <CommentPanel
            entry={commentEntry}
            teamMembers={allMembers}
            onClose={() => setCommentEntry(null)}
          />
        </div>
      )}
    </div>
  );
}

export default function Team() {
  const { user } = useAuth();
  const { allowed, requiredPlan } = useGate("team");
  const { data: teamData, loading, refetch } = useApi("/team");
  const toast = useToast();

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviting, setInviting] = useState(false);
  const [removing, setRemoving] = useState(null);

  const isOwner = !teamData?.is_member;
  const members = teamData?.members || [];
  const pending = teamData?.pending_invites || [];
  const limit = teamData?.limit || 3;
  const activeCount = members.filter((m) => m.accepted_at).length;

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    setInviting(true);
    try {
      await api.post("/team/invite", { email: inviteEmail, role: inviteRole });
      toast.success(`Invitación enviada a ${inviteEmail}`);
      setInviteEmail("");
      refetch();
    } catch (err) {
      toast.error(err.error || "Error al enviar invitación");
    } finally {
      setInviting(false);
    }
  };

  const handleRemove = async (memberId) => {
    setRemoving(memberId);
    try {
      await api.delete(`/team/members/${memberId}`);
      toast.success("Miembro removido");
      refetch();
    } catch (err) {
      toast.error(err.error || "Error al remover miembro");
    } finally {
      setRemoving(null);
    }
  };

  if (!allowed) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Equipo</h1>
        <UpgradePrompt feature="team" requiredPlan={requiredPlan}>
          <EmptyState
            icon={UsersThree}
            title="Gestión de equipo"
            description="Invita a tu equipo, asigna contratos y comenten juntos el pipeline en tiempo real."
          />
        </UpgradePrompt>
      </div>
    );
  }

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;

  const allMembers = [...members, ...pending];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Equipo</h1>

      <div className="flex flex-col lg:flex-row gap-6 min-h-0">
        {/* Left column — team management */}
        <div className="lg:w-72 flex-shrink-0 space-y-4">
          {/* Members card */}
          <Card className="p-5">
            <CardHeader title="Tu equipo" />

            {/* Owner info (shown when viewing as member) */}
            {teamData?.owner && teamData.is_member && (
              <div className="mb-3 px-3 py-2.5 bg-brand-50 rounded-xl flex items-center gap-2.5">
                <UserAvatar email={teamData.owner.email} size="md" />
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-brand-700 truncate">{teamData.owner.email}</p>
                  <p className="text-[10px] text-brand-500">Owner del equipo</p>
                </div>
              </div>
            )}

            {/* Active members */}
            {members.filter((m) => m.accepted_at).length > 0 ? (
              <div className="divide-y divide-surface-border">
                {members
                  .filter((m) => m.accepted_at)
                  .map((m) => (
                    <MemberRow
                      key={m.id}
                      member={m}
                      isOwner={isOwner}
                      onRemove={handleRemove}
                    />
                  ))}
              </div>
            ) : (
              <p className="text-xs text-ink-400 py-2">Sin miembros activos aún.</p>
            )}

            {/* Pending invites */}
            {pending.length > 0 && (
              <div className="mt-3 pt-3 border-t border-surface-border">
                <p className="text-[10px] font-semibold tracking-widest text-ink-400 uppercase mb-2">
                  Invitaciones pendientes
                </p>
                <div className="divide-y divide-surface-border">
                  {pending.map((inv) => (
                    <PendingRow
                      key={inv.id}
                      invite={inv}
                      isOwner={isOwner}
                      onCancel={handleRemove}
                    />
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* Invite card — only for owners */}
          {isOwner && (
            <Card className="p-5">
              <CardHeader title="Invitar miembro" />

              {/* Usage bar */}
              <div className="mb-4">
                <div className="flex justify-between text-xs text-ink-400 mb-1">
                  <span>Miembros activos</span>
                  <span className="font-semibold text-ink-700">{activeCount} / {limit}</span>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      activeCount >= limit ? "bg-red-400" : "bg-brand-500"
                    }`}
                    style={{ width: `${Math.min((activeCount / limit) * 100, 100)}%` }}
                  />
                </div>
              </div>

              {activeCount >= limit ? (
                <p className="text-xs text-red-600 text-center py-2">
                  Has alcanzado el límite de {limit} miembros. Actualiza tu plan para agregar más.
                </p>
              ) : (
                <form onSubmit={handleInvite} className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-ink-700 mb-1">Email</label>
                    <input
                      type="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="email@empresa.com"
                      className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400 outline-none"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-ink-700 mb-1">Rol</label>
                    <select
                      value={inviteRole}
                      onChange={(e) => setInviteRole(e.target.value)}
                      className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400 outline-none bg-white"
                    >
                      <option value="member">Miembro</option>
                      <option value="admin">Administrador</option>
                    </select>
                  </div>
                  <Button type="submit" disabled={inviting} className="w-full">
                    {inviting ? <Spinner className="h-4 w-4 mx-auto" /> : (
                      <span className="flex items-center justify-center gap-1.5">
                        <UserPlus size={14} /> Enviar invitación
                      </span>
                    )}
                  </Button>
                </form>
              )}
            </Card>
          )}
        </div>

        {/* Right column — shared pipeline */}
        <div className="flex-1 min-w-0 min-h-0">
          <Card className="p-5 h-full">
            <CardHeader title="Pipeline compartido">
              <span className="text-xs text-ink-400">
                {isOwner ? "Visible para todos tus miembros" : `Pipeline de ${teamData?.owner?.email || "tu equipo"}`}
              </span>
            </CardHeader>
            <div className="mt-4" style={{ height: "calc(100vh - 260px)", minHeight: 400 }}>
              <SharedPipeline ownerId={teamData?.owner?.id} teamMembers={allMembers} />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
