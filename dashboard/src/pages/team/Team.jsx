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
  UsersThree, UserPlus, X, Copy, CaretRight, ChatCircle,
  Kanban, TrendUp, CurrencyDollar, Trophy, Target,
  Crown, ArrowRight, CheckCircle, Lightning,
} from "@phosphor-icons/react";

const STAGES = [
  { key: "lead",      label: "Lead",      color: "gray" },
  { key: "proposal",  label: "Propuesta", color: "blue" },
  { key: "submitted", label: "Enviado",   color: "yellow" },
  { key: "won",       label: "Ganado",    color: "green" },
  { key: "lost",      label: "Perdido",   color: "red" },
];

// ─── Stats card ───────────────────────────────────────────────────────────────
function StatCard({ icon: Icon, iconBg, iconColor, label, value, sub }) {
  return (
    <div className="bg-white rounded-2xl border border-surface-border p-4 flex items-start gap-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${iconBg}`}>
        <Icon size={20} weight="duotone" className={iconColor} />
      </div>
      <div className="min-w-0">
        <p className="text-2xl font-bold text-ink-900 leading-tight tracking-tighter">{value}</p>
        <p className="text-xs font-medium text-ink-600 mt-0.5">{label}</p>
        {sub && <p className="text-[11px] text-ink-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ─── Member row ───────────────────────────────────────────────────────────────
function MemberRow({ member, isOwner, onRemove, pipelineEntries }) {
  const assigned = pipelineEntries.filter(e => e.assigned_to === member.member_user_id).length;
  const won = pipelineEntries.filter(e => e.assigned_to === member.member_user_id && e.stage === "won").length;

  return (
    <div className="flex items-center gap-3 py-3 border-b border-surface-border last:border-0">
      <UserAvatar email={member.email} size="md" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-ink-900 truncate">{member.email}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded-full ${
            member.role === "admin" ? "bg-purple-100 text-purple-700" : "bg-surface-hover text-ink-500"
          }`}>
            {member.role === "admin" ? "Admin" : "Miembro"}
          </span>
          {assigned > 0 && (
            <span className="text-[10px] text-ink-400">{assigned} asignados · {won} ganados</span>
          )}
        </div>
      </div>
      {isOwner && (
        <button
          onClick={() => onRemove(member.id)}
          className="p-1.5 rounded-lg hover:bg-red-50 text-ink-300 hover:text-red-500 transition-colors"
          title="Remover miembro"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

// ─── Pending row ──────────────────────────────────────────────────────────────
function PendingRow({ invite, isOwner, onCancel }) {
  const toast = useToast();
  const copyLink = () => {
    const url = `${window.location.origin}/team/accept/${invite.invite_token}`;
    navigator.clipboard.writeText(url).then(() => toast.success("Link copiado"));
  };

  return (
    <div className="flex items-center gap-3 py-3 border-b border-surface-border last:border-0">
      <div className="h-9 w-9 rounded-xl bg-surface-hover flex items-center justify-center flex-shrink-0">
        <span className="text-sm font-bold text-ink-400">{invite.email[0].toUpperCase()}</span>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-ink-700 truncate">{invite.email}</p>
        <p className="text-xs text-amber-500 font-medium">Pendiente de aceptar</p>
      </div>
      <button onClick={copyLink} className="p-1.5 rounded-lg hover:bg-surface-hover text-ink-300 hover:text-ink-600 transition-colors" title="Copiar link">
        <Copy size={13} />
      </button>
      {isOwner && (
        <button onClick={() => onCancel(invite.id)} className="p-1.5 rounded-lg hover:bg-red-50 text-ink-300 hover:text-red-500 transition-colors">
          <X size={14} />
        </button>
      )}
    </div>
  );
}

// ─── Comment panel ────────────────────────────────────────────────────────────
function CommentPanel({ entry, teamMembers, onClose }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [sending, setSending] = useState(false);
  const toast = useToast();

  const fetchComments = useCallback(async () => {
    try {
      const res = await api.get(`/pipeline/${entry.id}/comments`);
      setComments(res.comments || []);
    } catch { /* silent */ }
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

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border flex-shrink-0">
        <div>
          <p className="text-xs font-semibold text-ink-900 line-clamp-1">
            {entry.contract_title || `Contrato #${entry.contract_id}`}
          </p>
          <p className="text-[10px] text-ink-400">Comentarios del equipo</p>
        </div>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-surface-hover transition-colors text-ink-400">
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
            className="flex-1 rounded-xl border border-surface-border p-2.5 text-sm resize-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400 outline-none"
            rows={2}
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) sendComment(); }}
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

// ─── Shared Pipeline ──────────────────────────────────────────────────────────
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
  const allEntries = STAGES.flatMap(s => pipeline[s.key] || []);
  const isEmpty = allEntries.length === 0;
  const allMembers = teamMembers || [];

  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
        <div className="w-16 h-16 rounded-2xl bg-brand-50 flex items-center justify-center">
          <Kanban size={28} weight="duotone" className="text-brand-500" />
        </div>
        <div>
          <p className="text-sm font-semibold text-ink-900 mb-1">Pipeline compartido vacío</p>
          <p className="text-xs text-ink-400 max-w-xs">
            Agrega contratos a tu pipeline personal y aparecerán aquí automáticamente para todo tu equipo.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-4 h-full min-h-0">
      <div className={`flex-1 overflow-x-auto min-h-0 ${commentEntry ? "lg:max-w-[calc(100%-320px)]" : ""}`}>
        <div className="flex gap-3 min-w-max pb-2">
          {STAGES.map((stage) => (
            <div key={stage.key} className="w-52 space-y-2 flex-shrink-0">
              <div className="flex items-center gap-2 px-1">
                <Badge color={stage.color}>{stage.label}</Badge>
                <span className="text-xs text-ink-400 font-medium">{pipeline[stage.key]?.length || 0}</span>
              </div>
              {(pipeline[stage.key] || []).map((entry) => {
                const assignee = entry.assigned_to
                  ? allMembers.find((m) => m.member_user_id === entry.assigned_to)
                  : null;
                return (
                  <div key={entry.id} className="bg-white rounded-xl border border-surface-border p-3 space-y-2 hover:border-brand-200 transition-colors">
                    <p className="text-xs font-semibold text-ink-900 line-clamp-2 leading-snug">
                      {entry.contract_title || `Contrato #${entry.contract_id}`}
                    </p>
                    {entry.value && (
                      <p className="text-xs font-bold text-green-600">{money(entry.value)}</p>
                    )}
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
                          className="text-[10px] text-ink-300 hover:text-brand-600 transition-colors font-medium"
                        >
                          + Asignar
                        </button>
                      )}
                      <button
                        onClick={() => setCommentEntry(commentEntry?.id === entry.id ? null : entry)}
                        className={`ml-auto flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-lg transition-colors ${
                          commentEntry?.id === entry.id ? "bg-brand-100 text-brand-700" : "text-ink-300 hover:text-ink-600"
                        }`}
                      >
                        <ChatCircle size={11} />
                        {entry.comments_count > 0 && <span>{entry.comments_count}</span>}
                      </button>
                    </div>

                    {assigning === entry.id && (
                      <div className="border border-surface-border rounded-xl bg-white shadow-sm text-xs overflow-hidden">
                        <button onClick={() => handleAssign(entry.id, null)}
                          className="w-full text-left px-2.5 py-2 hover:bg-surface-hover text-ink-400">
                          Sin asignar
                        </button>
                        {allMembers.filter((m) => m.accepted_at).map((m) => (
                          <button key={m.id} onClick={() => handleAssign(entry.id, m.member_user_id)}
                            className="w-full text-left px-2.5 py-2 hover:bg-surface-hover flex items-center gap-2">
                            <UserAvatar email={m.email} size="sm" />
                            <span className="truncate">{m.email}</span>
                          </button>
                        ))}
                      </div>
                    )}

                    <div className="flex flex-wrap gap-1 pt-0.5">
                      {STAGES.filter((s) => s.key !== stage.key).map((s) => (
                        <button key={s.key} onClick={() => handleMove(entry.id, s.key)} disabled={!!moving}
                          className="text-[10px] px-1.5 py-0.5 rounded-lg bg-surface-hover hover:bg-surface-border text-ink-500 disabled:opacity-50 transition-colors">
                          <CaretRight size={9} className="inline" /> {s.label}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {commentEntry && (
        <div className="w-80 flex-shrink-0 bg-white rounded-2xl border border-surface-border flex flex-col overflow-hidden">
          <CommentPanel entry={commentEntry} teamMembers={allMembers} onClose={() => setCommentEntry(null)} />
        </div>
      )}
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export default function Team() {
  const { user } = useAuth();
  const { allowed, requiredPlan } = useGate("team");
  const { data: teamData, loading, refetch } = useApi("/team");
  const { data: pipelineData } = useApi("/team/pipeline");
  const toast = useToast();

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviting, setInviting] = useState(false);
  const [removing, setRemoving] = useState(null);

  const isOwner = !teamData?.is_member;
  const members = teamData?.members || [];
  const pending = teamData?.pending_invites || [];
  const limit = teamData?.limit || 3;
  const activeMembers = members.filter((m) => m.accepted_at);

  // Compute pipeline stats from team pipeline
  const allEntries = STAGES.flatMap(s => (pipelineData?.stages?.[s.key] || []));
  const totalContracts = allEntries.length;
  const totalValue = allEntries.reduce((sum, e) => sum + (e.value || 0), 0);
  const wonContracts = (pipelineData?.stages?.won || []).length;
  const activeContracts = allEntries.filter(e => !["won", "lost"].includes(e.stage)).length;

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
        <div>
          <h1 className="text-xl font-bold text-ink-900">Equipo</h1>
          <p className="text-sm text-ink-400 mt-1">Colabora con tu equipo en el pipeline de contratos</p>
        </div>
        <UpgradePrompt feature="team" requiredPlan={requiredPlan}>
          <div className="bg-white rounded-2xl border border-surface-border p-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              {[
                { icon: UsersThree, title: "Invita a tu equipo", desc: "Agrega hasta 5 colaboradores con roles diferenciados" },
                { icon: Kanban, title: "Pipeline compartido", desc: "Todos ven el mismo tablero Kanban en tiempo real" },
                { icon: ChatCircle, title: "Comenten juntos", desc: "Deja comentarios en cada contrato del pipeline" },
              ].map(({ icon: Icon, title, desc }) => (
                <div key={title} className="text-center p-4">
                  <div className="w-12 h-12 rounded-2xl bg-brand-50 flex items-center justify-center mx-auto mb-3">
                    <Icon size={22} weight="duotone" className="text-brand-500" />
                  </div>
                  <p className="text-sm font-semibold text-ink-900 mb-1">{title}</p>
                  <p className="text-xs text-ink-400">{desc}</p>
                </div>
              ))}
            </div>
            <EmptyState
              icon={UsersThree}
              title="Disponible desde el plan Estratega"
              description="Gestiona tu equipo, asigna contratos y ganen más juntos."
            />
          </div>
        </UpgradePrompt>
      </div>
    );
  }

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;

  const allMembers = [...members, ...pending];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-ink-900">Equipo</h1>
          <p className="text-sm text-ink-400 mt-0.5">
            {isOwner
              ? `${activeMembers.length} miembro${activeMembers.length !== 1 ? "s" : ""} activo${activeMembers.length !== 1 ? "s" : ""} · Tú eres el owner`
              : `Pipeline de ${teamData?.owner?.email || "tu equipo"}`}
          </p>
        </div>
      </div>

      {/* Stats row */}
      {totalContracts > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatCard
            icon={Target}
            iconBg="bg-brand-50"
            iconColor="text-brand-600"
            label="Contratos activos"
            value={activeContracts}
            sub="En seguimiento"
          />
          <StatCard
            icon={CurrencyDollar}
            iconBg="bg-green-50"
            iconColor="text-green-600"
            label="Valor del pipeline"
            value={totalValue > 0 ? `$${(totalValue / 1_000_000).toFixed(0)}M` : "—"}
            sub="COP estimado"
          />
          <StatCard
            icon={Trophy}
            iconBg="bg-amber-50"
            iconColor="text-amber-600"
            label="Contratos ganados"
            value={wonContracts}
            sub={totalContracts > 0 ? `${Math.round((wonContracts / totalContracts) * 100)}% win rate` : "—"}
          />
          <StatCard
            icon={UsersThree}
            iconBg="bg-purple-50"
            iconColor="text-purple-600"
            label="Miembros activos"
            value={activeMembers.length}
            sub={`Límite: ${limit}`}
          />
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-col lg:flex-row gap-5 min-h-0">

        {/* Left: Team management */}
        <div className="lg:w-64 flex-shrink-0 space-y-4">

          {/* Members */}
          <div className="bg-white rounded-2xl border border-surface-border p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-bold text-ink-900">Tu equipo</p>
              <span className="text-xs text-ink-400 bg-surface-hover px-2 py-0.5 rounded-full">
                {activeMembers.length}/{limit}
              </span>
            </div>

            {/* Owner (when viewing as member) */}
            {teamData?.owner && teamData.is_member && (
              <div className="mb-3 px-3 py-2.5 bg-brand-50 rounded-xl flex items-center gap-2.5">
                <UserAvatar email={teamData.owner.email} size="md" />
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold text-brand-700 truncate">{teamData.owner.email}</p>
                  <div className="flex items-center gap-1 mt-0.5">
                    <Crown size={10} className="text-amber-500" weight="fill" />
                    <p className="text-[10px] text-brand-500">Owner</p>
                  </div>
                </div>
              </div>
            )}

            {activeMembers.length > 0 ? (
              <div>
                {activeMembers.map((m) => (
                  <MemberRow
                    key={m.id}
                    member={m}
                    isOwner={isOwner}
                    onRemove={handleRemove}
                    pipelineEntries={allEntries}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-4">
                <UsersThree size={24} className="text-ink-200 mx-auto mb-2" />
                <p className="text-xs text-ink-400">Sin miembros aún</p>
              </div>
            )}

            {/* Pending invites */}
            {pending.length > 0 && (
              <div className="mt-3 pt-3 border-t border-surface-border">
                <p className="text-[10px] font-bold tracking-widest text-ink-300 uppercase mb-2">
                  Invitaciones pendientes
                </p>
                {pending.map((inv) => (
                  <PendingRow key={inv.id} invite={inv} isOwner={isOwner} onCancel={handleRemove} />
                ))}
              </div>
            )}
          </div>

          {/* Invite form — only for owners */}
          {isOwner && (
            <div className="bg-white rounded-2xl border border-surface-border p-4">
              <p className="text-sm font-bold text-ink-900 mb-3 flex items-center gap-1.5">
                <UserPlus size={15} className="text-brand-500" />
                Invitar miembro
              </p>

              {/* Usage bar */}
              <div className="mb-4">
                <div className="h-1.5 bg-surface-border rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${activeMembers.length >= limit ? "bg-red-400" : "bg-brand-500"}`}
                    style={{ width: `${Math.min((activeMembers.length / limit) * 100, 100)}%` }}
                  />
                </div>
                <p className="text-[10px] text-ink-400 mt-1">{activeMembers.length} de {limit} miembros usados</p>
              </div>

              {activeMembers.length >= limit ? (
                <div className="text-center py-2">
                  <p className="text-xs text-red-600 mb-2">Has alcanzado el límite de {limit} miembros.</p>
                  <Button variant="secondary" size="sm" className="w-full">
                    <Lightning size={13} weight="duotone" /> Actualizar plan
                  </Button>
                </div>
              ) : (
                <form onSubmit={handleInvite} className="space-y-2.5">
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="email@empresa.com"
                    className="w-full rounded-xl border border-surface-border px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400 outline-none"
                    required
                  />
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full rounded-xl border border-surface-border px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400 outline-none bg-white"
                  >
                    <option value="member">Miembro — puede ver y comentar</option>
                    <option value="admin">Admin — puede mover y asignar</option>
                  </select>
                  <Button type="submit" disabled={inviting} className="w-full justify-center">
                    {inviting ? <Spinner className="h-4 w-4 mx-auto" /> : (
                      <><UserPlus size={14} /> Enviar invitación</>
                    )}
                  </Button>
                </form>
              )}
            </div>
          )}

          {/* Role guide */}
          <div className="bg-surface-bg rounded-2xl border border-surface-border p-4">
            <p className="text-xs font-bold text-ink-500 uppercase tracking-widest mb-3">¿Para qué sirve el equipo?</p>
            <div className="space-y-2.5">
              {[
                { icon: Kanban, text: "Pipeline compartido en tiempo real" },
                { icon: ChatCircle, text: "Comenten contratos juntos" },
                { icon: Target, text: "Asigna contratos a cada persona" },
                { icon: TrendUp, text: "Ve el progreso de todo el equipo" },
              ].map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-center gap-2 text-xs text-ink-600">
                  <Icon size={13} className="text-brand-500 flex-shrink-0" weight="duotone" />
                  {text}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Pipeline */}
        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-2xl border border-surface-border p-5 h-full">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm font-bold text-ink-900">Pipeline compartido</p>
                <p className="text-xs text-ink-400 mt-0.5">
                  {isOwner ? "Visible para todos tus miembros en tiempo real" : `Pipeline de ${teamData?.owner?.email || "tu equipo"}`}
                </p>
              </div>
              {totalContracts > 0 && (
                <span className="text-xs bg-surface-hover text-ink-500 font-medium px-2.5 py-1 rounded-full">
                  {totalContracts} contratos
                </span>
              )}
            </div>
            <div style={{ height: "calc(100vh - 320px)", minHeight: 380 }}>
              <SharedPipeline ownerId={teamData?.owner?.id} teamMembers={allMembers} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
