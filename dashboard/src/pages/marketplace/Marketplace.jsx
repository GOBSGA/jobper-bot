import { useState, useEffect, useRef } from "react";
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
import { Store, Plus, Star, MessageCircle, Send, Inbox, ArrowLeft, Circle } from "lucide-react";
import { useGate } from "../../hooks/useGate";
import UpgradePrompt from "../../components/ui/UpgradePrompt";
import { useAuth } from "../../context/AuthContext";

// ─── Chat panel ───────────────────────────────────────────────────────────────
function ChatPanel({ contract, onClose }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);
  const pollRef = useRef(null);

  const fetchMessages = async () => {
    try {
      const data = await api.get(`/marketplace/${contract.id}/messages`);
      setMessages(data.messages || []);
    } catch {
      // silently ignore — polling will retry
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
    // Poll every 5 seconds while chat is open
    pollRef.current = setInterval(fetchMessages, 5000);
    return () => clearInterval(pollRef.current);
  }, [contract.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (e) => {
    e.preventDefault();
    const content = text.trim();
    if (!content || sending) return;
    setSending(true);
    const optimistic = {
      id: `tmp-${Date.now()}`,
      sender_id: user?.id,
      is_mine: true,
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);
    setText("");
    try {
      const msg = await api.post(`/marketplace/${contract.id}/messages`, { content });
      setMessages((prev) =>
        prev.map((m) => (m.id === optimistic.id ? { ...msg, is_mine: true } : m))
      );
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== optimistic.id));
      setText(content);
    } finally {
      setSending(false);
    }
  };

  const fmt = (iso) => {
    const d = new Date(iso);
    return d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-gray-100">
        <button onClick={onClose} className="p-1 rounded hover:bg-gray-100">
          <ArrowLeft className="h-4 w-4 text-gray-500" />
        </button>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate">{contract.title}</p>
          {contract.budget_min && (
            <p className="text-xs text-gray-500">{money(contract.budget_min)}</p>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2 min-h-0">
        {loading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : messages.length === 0 ? (
          <p className="text-center text-xs text-gray-400 py-8">
            Inicia la conversación sobre este contrato
          </p>
        ) : (
          messages.map((m) => (
            <div key={m.id} className={`flex ${m.is_mine ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[75%] rounded-2xl px-3 py-2 text-sm ${
                  m.is_mine
                    ? "bg-brand-600 text-white rounded-br-sm"
                    : "bg-gray-100 text-gray-900 rounded-bl-sm"
                }`}
              >
                <p className="leading-snug">{m.content}</p>
                <p
                  className={`text-[10px] mt-0.5 text-right ${
                    m.is_mine ? "text-white/70" : "text-gray-400"
                  }`}
                >
                  {fmt(m.created_at)}
                </p>
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={send} className="flex gap-2 p-3 border-t border-gray-100">
        <input
          className="flex-1 rounded-full border border-gray-300 px-4 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
          placeholder="Escribe un mensaje..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={sending}
          maxLength={2000}
          autoFocus
        />
        <button
          type="submit"
          disabled={!text.trim() || sending}
          className="p-2 rounded-full bg-brand-600 text-white disabled:opacity-40 hover:bg-brand-700 transition"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}

// ─── Inbox view ───────────────────────────────────────────────────────────────
function InboxView({ onSelectContract, onClose }) {
  const { data, loading } = useApi("/marketplace/inbox");

  if (loading) return <div className="flex justify-center py-8"><Spinner /></div>;

  const convs = data?.conversations || [];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 p-4 border-b border-gray-100">
        <button onClick={onClose} className="p-1 rounded hover:bg-gray-100">
          <ArrowLeft className="h-4 w-4 text-gray-500" />
        </button>
        <p className="text-sm font-semibold text-gray-900">Mensajes</p>
        {data?.total_unread > 0 && (
          <span className="ml-auto text-xs bg-red-500 text-white rounded-full px-2 py-0.5">
            {data.total_unread}
          </span>
        )}
      </div>

      {convs.length === 0 ? (
        <p className="text-center text-xs text-gray-400 py-8">Sin conversaciones aún</p>
      ) : (
        <div className="overflow-y-auto divide-y divide-gray-50">
          {convs.map((c) => (
            <button
              key={c.contract_id}
              className="w-full text-left px-4 py-3 hover:bg-gray-50 flex items-start gap-3"
              onClick={() => onSelectContract({ id: c.contract_id, title: c.title })}
            >
              <MessageCircle className="h-5 w-5 text-gray-400 mt-0.5 flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900 truncate">{c.title}</p>
                {c.last_msg && (
                  <p className="text-xs text-gray-500 truncate mt-0.5">{c.last_msg}</p>
                )}
              </div>
              {c.unread > 0 && (
                <span className="flex-shrink-0 h-5 w-5 rounded-full bg-brand-600 text-white text-[10px] flex items-center justify-center">
                  {c.unread}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function Marketplace() {
  const { allowed, requiredPlan } = useGate("marketplace");
  const { data, loading, refetch } = useApi("/marketplace");
  const { data: inboxData } = useApi("/marketplace/inbox");
  const toast = useToast();
  const [showPublish, setShowPublish] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", budget_min: "", category: "", contact_phone: "", city: "" });
  const [publishing, setPublishing] = useState(false);

  // Chat state
  const [chatContract, setChatContract] = useState(null); // { id, title, budget_min }
  const [showInbox, setShowInbox] = useState(false);

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

  const openChat = (c) => {
    setChatContract(c);
    setShowInbox(false);
  };

  const totalUnread = inboxData?.total_unread || 0;

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

  // Chat panel overlay
  if (chatContract) {
    return (
      <div className="space-y-6">
        <Card className="h-[600px] flex flex-col overflow-hidden p-0">
          <ChatPanel contract={chatContract} onClose={() => setChatContract(null)} />
        </Card>
      </div>
    );
  }

  // Inbox overlay
  if (showInbox) {
    return (
      <div className="space-y-6">
        <Card className="h-[600px] flex flex-col overflow-hidden p-0">
          <InboxView
            onSelectContract={openChat}
            onClose={() => setShowInbox(false)}
          />
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Marketplace</h1>
        <div className="flex gap-2">
          {/* Inbox button with unread badge */}
          <button
            onClick={() => setShowInbox(true)}
            className="relative p-2 rounded-lg border border-gray-200 hover:bg-gray-50"
            title="Mensajes"
          >
            <MessageCircle className="h-5 w-5 text-gray-600" />
            {totalUnread > 0 && (
              <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 text-white text-[9px] flex items-center justify-center font-bold">
                {totalUnread > 9 ? "9+" : totalUnread}
              </span>
            )}
          </button>
          <Button onClick={() => setShowPublish(true)}><Plus className="h-4 w-4" /> Publicar</Button>
        </div>
      </div>

      {!data?.results?.length ? (
        <EmptyState
          icon={Store}
          title="Marketplace vacío"
          description="Sé el primero en publicar un contrato o servicio."
          action={<Button onClick={() => setShowPublish(true)}>Publicar ahora</Button>}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.results.map((c) => (
            <Card key={c.id} className="space-y-3">
              <div className="flex items-start justify-between">
                <h3 className="text-sm font-semibold text-gray-900 line-clamp-2">{c.title}</h3>
                {c.is_featured && <Star className="h-4 w-4 text-yellow-500 fill-yellow-500 flex-shrink-0" />}
              </div>
              {c.category && <p className="text-xs text-gray-500">{c.category}</p>}
              {c.city && <p className="text-xs text-gray-400">{c.city}</p>}
              {c.budget_min && (
                <p className="text-sm font-bold text-gray-900">
                  {money(c.budget_min)}{c.budget_max ? ` - ${money(c.budget_max)}` : ""}
                </p>
              )}
              {c.description && <p className="text-xs text-gray-600 line-clamp-3">{c.description}</p>}
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => openChat(c)}
                >
                  <MessageCircle className="h-3 w-3" /> Contactar
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

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
