import { useState, useEffect, useRef, useCallback } from "react";
import { useApi } from "../../hooks/useApi";
import { api } from "../../lib/api";
import { useToast } from "../../components/ui/Toast";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Modal from "../../components/ui/Modal";
import Input from "../../components/ui/Input";
import EmptyState from "../../components/ui/EmptyState";
import { SkeletonMarketplaceCard } from "../../components/ui/Skeleton";
import { money, relative } from "../../lib/format";
import {
  Storefront, ChatCircle, PaperPlaneTilt, ArrowLeft,
  Plus, Star, Tray, Check, Checks, ArrowRight, X,
} from "@phosphor-icons/react";
import { useGate } from "../../hooks/useGate";
import UpgradePrompt from "../../components/ui/UpgradePrompt";
import { useAuth } from "../../context/AuthContext";

// ─── Chat panel ───────────────────────────────────────────────────────────────
function ChatPanel({ contract, onClose, isMobile }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);
  const pollRef = useRef(null);
  const inputRef = useRef(null);

  const fetchMessages = useCallback(async () => {
    try {
      const data = await api.get(`/marketplace/${contract.id}/messages`);
      setMessages(data.messages || []);
    } catch {
      // polling retries silently
    } finally {
      setLoading(false);
    }
  }, [contract.id]);

  useEffect(() => {
    setMessages([]);
    setLoading(true);
    fetchMessages();
    pollRef.current = setInterval(fetchMessages, 2000);
    return () => clearInterval(pollRef.current);
  }, [contract.id, fetchMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [contract.id]);

  const send = async (e) => {
    e?.preventDefault();
    const content = text.trim();
    if (!content || sending) return;
    setSending(true);
    const optimistic = {
      id: `tmp-${Date.now()}`,
      sender_id: user?.id,
      is_mine: true,
      content,
      created_at: new Date().toISOString(),
      read_at: null,
    };
    setMessages((prev) => [...prev, optimistic]);
    setText("");
    try {
      const msg = await api.post(`/marketplace/${contract.id}/messages`, { content });
      setMessages((prev) =>
        prev.map((m) => (m.id === optimistic.id ? { ...msg, is_mine: true } : m))
      );
    } catch {
      setMessages((prev) => prev.filter((m) => m.id !== optimistic.id));
      setText(content);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const fmt = (iso) =>
    new Date(iso).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Contract context header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-surface-border bg-white flex-shrink-0">
        <button
          onClick={onClose}
          className="p-1.5 rounded-xl hover:bg-surface-hover transition-colors flex-shrink-0"
        >
          <ArrowLeft size={16} className="text-ink-400" />
        </button>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-ink-900 truncate leading-snug">{contract.title}</p>
          <div className="flex items-center gap-2 mt-0.5">
            {contract.budget_min && (
              <span className="text-2xs font-medium text-accent-700">{money(contract.budget_min)}</span>
            )}
            {contract.city && (
              <span className="text-2xs text-ink-400">{contract.city}</span>
            )}
            {contract.category && (
              <span className="text-2xs text-ink-400">{contract.category}</span>
            )}
          </div>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1.5 min-h-0 bg-surface-bg">
        {loading ? (
          <div className="flex flex-col gap-3 pt-4">
            {[70, 50, 75, 45].map((w, i) => (
              <div key={i} className={`flex ${i % 2 === 0 ? "justify-start" : "justify-end"}`}>
                <div
                  className="animate-pulse bg-surface-border rounded-2xl h-9"
                  style={{ width: `${w}%` }}
                />
              </div>
            ))}
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <div className="w-12 h-12 rounded-2xl bg-brand-50 flex items-center justify-center">
              <ChatCircle size={22} weight="duotone" className="text-brand-500" />
            </div>
            <p className="text-sm font-medium text-ink-900">Inicia la conversación</p>
            <p className="text-xs text-ink-400 text-center max-w-xs">
              Presenta tu empresa y propuesta para este contrato
            </p>
          </div>
        ) : (
          messages.map((m) => (
            <div key={m.id} className={`flex ${m.is_mine ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[78%] rounded-2xl px-3.5 py-2.5 ${
                  m.is_mine
                    ? "bg-brand-500 text-white rounded-br-sm"
                    : "bg-white border border-surface-border text-ink-900 rounded-bl-sm"
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{m.content}</p>
                <div className={`flex items-center justify-end gap-1 mt-1 ${m.is_mine ? "text-white/60" : "text-ink-400"}`}>
                  <span className="text-[10px]">{fmt(m.created_at)}</span>
                  {m.is_mine && (
                    m.read_at
                      ? <Checks size={11} weight="bold" className="text-white/80" />
                      : <Check size={11} weight="bold" className="text-white/60" />
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input composer */}
      <div className="flex items-end gap-2 px-3 py-3 border-t border-surface-border bg-white flex-shrink-0">
        <textarea
          ref={inputRef}
          rows={1}
          className="flex-1 resize-none rounded-2xl border border-surface-border bg-surface-bg px-4 py-2.5 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-300 focus:ring-1 focus:ring-brand-200 outline-none transition-colors min-h-[42px] max-h-32 overflow-y-auto"
          placeholder="Escribe tu mensaje... (Enter para enviar)"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={sending}
          maxLength={2000}
        />
        <button
          onClick={send}
          disabled={!text.trim() || sending}
          className="flex-shrink-0 w-10 h-10 rounded-xl bg-brand-500 text-white flex items-center justify-center hover:bg-brand-600 disabled:opacity-40 transition-colors"
        >
          <PaperPlaneTilt size={16} weight="fill" />
        </button>
      </div>
    </div>
  );
}

// ─── Conversation list (inbox sidebar) ────────────────────────────────────────
function ConversationList({ activeId, onSelectContract, onClose }) {
  const { data, loading } = useApi("/marketplace/inbox");
  const convs = data?.conversations || [];

  const fmt = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    const now = new Date();
    const diffH = (now - d) / 3600000;
    if (diffH < 1) return `${Math.floor(diffH * 60)}m`;
    if (diffH < 24) return `${Math.floor(diffH)}h`;
    return d.toLocaleDateString("es-CO", { day: "numeric", month: "short" });
  };

  return (
    <div className="flex flex-col h-full min-h-0 border-r border-surface-border bg-white">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-surface-border flex-shrink-0">
        <p className="text-sm font-bold text-ink-900 flex-1">Mensajes</p>
        {data?.total_unread > 0 && (
          <span className="text-2xs bg-brand-500 text-white rounded-full px-1.5 py-0.5 font-bold">
            {data.total_unread}
          </span>
        )}
        {onClose && (
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-surface-hover transition-colors">
            <X size={14} className="text-ink-400" />
          </button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-3">
                <div className="animate-pulse bg-surface-border rounded-xl w-9 h-9 flex-shrink-0" />
                <div className="flex-1 space-y-2 pt-1">
                  <div className="animate-pulse bg-surface-border rounded h-3 w-3/4" />
                  <div className="animate-pulse bg-surface-border rounded h-2.5 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : convs.length === 0 ? (
          <p className="text-xs text-ink-400 text-center py-10">Sin conversaciones aún</p>
        ) : (
          convs.map((c) => (
            <button
              key={c.contract_id}
              onClick={() => onSelectContract({ id: c.contract_id, title: c.title })}
              className={`w-full text-left px-4 py-3 flex items-start gap-3 transition-colors hover:bg-surface-hover border-b border-surface-border/50 ${
                activeId === c.contract_id ? "bg-brand-50" : ""
              }`}
            >
              {/* Avatar */}
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-sm font-bold ${
                activeId === c.contract_id ? "bg-brand-100 text-brand-700" : "bg-surface-hover text-ink-600"
              }`}>
                {(c.title || "?")[0].toUpperCase()}
              </div>
              {/* Content */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-1">
                  <p className="text-xs font-semibold text-ink-900 truncate">{c.title}</p>
                  {c.last_msg_at && (
                    <span className="text-[10px] text-ink-400 flex-shrink-0">{fmt(c.last_msg_at)}</span>
                  )}
                </div>
                {c.last_msg && (
                  <p className="text-[11px] text-ink-400 truncate mt-0.5">{c.last_msg}</p>
                )}
              </div>
              {/* Unread badge */}
              {c.unread > 0 && (
                <span className="flex-shrink-0 min-w-[18px] h-[18px] rounded-full bg-brand-500 text-white text-[9px] font-bold flex items-center justify-center px-1">
                  {c.unread > 9 ? "9+" : c.unread}
                </span>
              )}
            </button>
          ))
        )}
      </div>
    </div>
  );
}

// ─── Marketplace card ─────────────────────────────────────────────────────────
function MarketplaceCard({ c, onContact }) {
  return (
    <div className="bg-white rounded-2xl border border-surface-border p-5 flex flex-col gap-3 hover:border-brand-200 transition-colors">
      {/* Title row */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-ink-900 line-clamp-2 flex-1 leading-snug">{c.title}</h3>
        {c.is_featured && (
          <Star size={15} weight="fill" className="text-amber-400 flex-shrink-0 mt-0.5" />
        )}
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-1.5">
        {c.category && (
          <span className="text-2xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-600 font-medium">
            {c.category}
          </span>
        )}
        {c.city && (
          <span className="text-2xs px-2 py-0.5 rounded-full bg-surface-hover text-ink-600 font-medium">
            {c.city}
          </span>
        )}
      </div>

      {/* Description */}
      {c.description && (
        <p className="text-xs text-ink-600 line-clamp-2 leading-relaxed">{c.description}</p>
      )}

      {/* Budget */}
      {(c.budget_min || c.budget_max) && (
        <p className="text-base font-bold text-ink-900 tracking-tighter">
          {c.budget_min ? money(c.budget_min) : ""}
          {c.budget_min && c.budget_max ? " – " : ""}
          {c.budget_max ? money(c.budget_max) : ""}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-1 border-t border-surface-border mt-auto">
        <span className="text-2xs text-ink-400">
          {c.created_at ? relative(c.created_at) : ""}
        </span>
        <Button size="sm" onClick={() => onContact(c)}>
          Contactar <ArrowRight size={12} />
        </Button>
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function Marketplace() {
  const { allowed, requiredPlan } = useGate("marketplace");
  const { data, loading, refetch } = useApi("/marketplace");
  const { data: inboxData, refetch: refetchInbox } = useApi("/marketplace/inbox");
  const toast = useToast();
  const [showPublish, setShowPublish] = useState(false);
  const [form, setForm] = useState({
    title: "", description: "", budget_min: "", budget_max: "",
    category: "", contact_phone: "", city: "",
  });
  const [publishing, setPublishing] = useState(false);
  const [chatContract, setChatContract] = useState(null);
  const [showInboxMobile, setShowInboxMobile] = useState(false);

  const totalUnread = inboxData?.total_unread || 0;

  const openChat = (c) => {
    setChatContract(c);
    setShowInboxMobile(false);
    refetchInbox();
  };

  const closeChat = () => {
    setChatContract(null);
    refetchInbox();
  };

  const publish = async (e) => {
    e.preventDefault();
    setPublishing(true);
    try {
      await api.post("/marketplace", {
        title: form.title,
        description: form.description || undefined,
        budget_min: form.budget_min ? Number(form.budget_min) : undefined,
        budget_max: form.budget_max ? Number(form.budget_max) : undefined,
        category: form.category || undefined,
        contact_phone: form.contact_phone || undefined,
        city: form.city || undefined,
      });
      setShowPublish(false);
      setForm({ title: "", description: "", budget_min: "", budget_max: "", category: "", contact_phone: "", city: "" });
      toast.success("Contrato publicado");
      refetch();
    } catch (err) {
      toast.error(err.error || "Error al publicar");
    } finally {
      setPublishing(false);
    }
  };

  if (!allowed) {
    return (
      <div className="space-y-6">
        <h1 className="text-xl font-bold text-ink-900">Marketplace</h1>
        <UpgradePrompt feature="marketplace" requiredPlan={requiredPlan}>
          <EmptyState
            icon={Storefront}
            title="Marketplace de contratos"
            description="Publica tus servicios y conecta con contratistas para tus proyectos."
          />
        </UpgradePrompt>
      </div>
    );
  }

  // ── MOBILE: full-screen inbox ──
  if (showInboxMobile) {
    return (
      <div className="lg:hidden fixed inset-0 z-40 bg-white flex flex-col" style={{ top: 0 }}>
        <ConversationList
          activeId={chatContract?.id}
          onSelectContract={openChat}
          onClose={() => setShowInboxMobile(false)}
        />
      </div>
    );
  }

  // ── MOBILE: full-screen chat ──
  if (chatContract) {
    return (
      <>
        {/* Mobile: full screen */}
        <div className="lg:hidden fixed inset-0 z-40 bg-surface-bg flex flex-col" style={{ top: 0 }}>
          <ChatPanel contract={chatContract} onClose={closeChat} isMobile />
        </div>

        {/* Desktop: split layout */}
        <div className="hidden lg:flex flex-col gap-0">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-bold text-ink-900">Marketplace</h1>
            <div className="flex gap-2">
              <button
                onClick={() => setShowPublish(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-surface-border text-xs font-medium text-ink-600 hover:bg-surface-hover transition-colors"
              >
                <Plus size={13} /> Publicar
              </button>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-surface-border overflow-hidden" style={{ height: "calc(100vh - 200px)" }}>
            <div className="flex h-full">
              {/* Left: conversation list */}
              <div className="w-72 flex-shrink-0">
                <ConversationList
                  activeId={chatContract?.id}
                  onSelectContract={openChat}
                />
              </div>
              {/* Right: chat */}
              <div className="flex-1 min-w-0 border-l border-surface-border">
                <ChatPanel contract={chatContract} onClose={closeChat} />
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  // ── Main marketplace view ──
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-ink-900">Marketplace</h1>
        <div className="flex items-center gap-2">
          {/* Inbox button */}
          <button
            onClick={() => {
              if (window.innerWidth < 1024) setShowInboxMobile(true);
              else if (inboxData?.conversations?.length > 0) openChat(inboxData.conversations[0]);
            }}
            className="relative p-2 rounded-xl border border-surface-border hover:bg-surface-hover transition-colors"
            title="Mensajes"
          >
            <ChatCircle size={18} className="text-ink-600" />
            {totalUnread > 0 && (
              <span className="absolute -top-1 -right-1 min-w-[16px] h-4 rounded-full bg-brand-500 text-white text-[9px] font-bold flex items-center justify-center px-0.5">
                {totalUnread > 9 ? "9+" : totalUnread}
              </span>
            )}
          </button>
          <Button onClick={() => setShowPublish(true)} size="sm">
            <Plus size={14} /> Publicar
          </Button>
        </div>
      </div>

      {/* Cards grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => <SkeletonMarketplaceCard key={i} />)}
        </div>
      ) : !data?.results?.length ? (
        <EmptyState
          icon={Storefront}
          title="Marketplace vacío"
          description="Sé el primero en publicar un contrato o servicio."
          action={<Button onClick={() => setShowPublish(true)}>Publicar ahora</Button>}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.results.map((c) => (
            <MarketplaceCard key={c.id} c={c} onContact={openChat} />
          ))}
        </div>
      )}

      {/* Publish modal */}
      {showPublish && (
        <Modal open onClose={() => setShowPublish(false)} title="Publicar contrato">
          <form onSubmit={publish} className="space-y-4">
            <Input
              label="Título *"
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="Ej: Necesito empresa de construcción para obra civil"
              required
            />
            <div>
              <label className="block text-xs font-medium text-ink-700 mb-1">Descripción</label>
              <textarea
                className="w-full rounded-xl border border-surface-border px-3 py-2 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-300 focus:ring-1 focus:ring-brand-200 outline-none resize-none"
                rows={3}
                placeholder="Describe el contrato, requisitos, experiencia necesaria..."
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Presupuesto mínimo (COP)"
                type="number"
                value={form.budget_min}
                onChange={(e) => setForm((f) => ({ ...f, budget_min: e.target.value }))}
                placeholder="50000000"
              />
              <Input
                label="Presupuesto máximo (COP)"
                type="number"
                value={form.budget_max}
                onChange={(e) => setForm((f) => ({ ...f, budget_max: e.target.value }))}
                placeholder="200000000"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Categoría"
                value={form.category}
                onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                placeholder="Ej: Construcción"
              />
              <Input
                label="Ciudad"
                value={form.city}
                onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))}
                placeholder="Ej: Bogotá"
              />
            </div>
            <Input
              label="Teléfono de contacto"
              value={form.contact_phone}
              onChange={(e) => setForm((f) => ({ ...f, contact_phone: e.target.value }))}
              placeholder="+57 300 000 0000"
            />
            <div className="flex gap-2 pt-2">
              <Button type="submit" className="flex-1 justify-center" disabled={publishing || !form.title}>
                {publishing ? "Publicando..." : "Publicar contrato"}
              </Button>
              <Button type="button" variant="secondary" onClick={() => setShowPublish(false)}>
                Cancelar
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
