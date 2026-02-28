import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import Card from "../../components/ui/Card";
import Input from "../../components/ui/Input";
import {
  Robot,
  Clock,
  EnvelopeSimple,
  Lightning,
  PaperPlaneTilt,
  Question,
  Buildings,
  FileText,
  CreditCard,
  Gear,
  ArrowsClockwise,
} from "@phosphor-icons/react";

const SUPPORT_EMAIL = "soporte@jobper.co";

const QUICK_QUESTIONS = [
  { icon: FileText, text: "¿Cómo funciona la búsqueda de contratos?" },
  { icon: CreditCard, text: "¿Cómo pago mi suscripción?" },
  { icon: Buildings, text: "¿Qué diferencia hay entre los planes?" },
  { icon: Gear, text: "¿Cómo configuro mis alertas?" },
  { icon: Question, text: "¿Qué es el score de compatibilidad?" },
];

export default function Support() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "¡Hola! Soy el asistente de Jobper. Puedo ayudarte con preguntas sobre la plataforma, estrategias de licitación y más. ¿En qué te puedo ayudar?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [remaining, setRemaining] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const escalate = () => {
    const subject = encodeURIComponent("Soporte Jobper — Consulta");
    const body = encodeURIComponent(
      "Hola equipo de Jobper,\n\nNecesito ayuda con:\n\n[Describe tu problema aquí]\n\nGracias."
    );
    window.open(`mailto:${SUPPORT_EMAIL}?subject=${subject}&body=${body}`, "_blank");
  };

  const send = async (text) => {
    const q = (text !== undefined ? text : input).trim();
    if (!q || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await api.post("/support/chat", { question: q });
      if (res.messages_remaining != null) setRemaining(res.messages_remaining);
      setMessages((m) => [...m, { role: "bot", text: res.answer }]);
      if (res.suggestions?.length) {
        setMessages((m) => [
          ...m,
          {
            role: "bot",
            text: "Preguntas sugeridas:\n" + res.suggestions.map((s) => `• ${s}`).join("\n"),
            isSuggestions: true,
          },
        ]);
      }
      if (res.rate_limited) setRemaining(0);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "bot",
          text: "Ocurrió un error. Intenta de nuevo o escríbenos a soporte@jobper.co.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    send();
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const isRateLimited = remaining === 0;

  return (
    <div className="flex flex-col lg:flex-row gap-5 pb-6 h-full">
      {/* ── Left panel: info + quick questions ── */}
      <div className="lg:w-72 xl:w-80 flex-shrink-0 space-y-4">
        {/* Title */}
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Robot size={22} className="text-brand-600" weight="duotone" />
            <h1 className="text-xl font-bold text-ink-900">Asistente Jobper</h1>
          </div>
          <p className="text-sm text-ink-400">Respuestas instantáneas 24/7</p>
        </div>

        {/* SLA */}
        <Card className="p-4 !bg-blue-50 !border-blue-100">
          <div className="flex items-start gap-3">
            <Clock size={15} className="text-blue-500 flex-shrink-0 mt-0.5" weight="fill" />
            <p className="text-xs text-blue-800 leading-relaxed">
              Asistente disponible <strong>24/7</strong>. Soporte humano:{" "}
              <strong>6:00 AM y 4:00 PM</strong> (Colombia, lun–vie).
            </p>
          </div>
        </Card>

        {/* Remaining */}
        {remaining !== null && (
          <div
            className={`flex items-center justify-between px-3 py-2 rounded-xl border text-xs font-medium ${
              remaining <= 2
                ? "bg-amber-50 border-amber-200 text-amber-700"
                : "bg-surface-hover border-surface-border text-ink-400"
            }`}
          >
            <span>
              {remaining > 0 ? `${remaining} consultas restantes hoy` : "Límite diario alcanzado"}
            </span>
            {remaining <= 2 && (
              <Link to="/payments" className="flex items-center gap-0.5 text-brand-600 hover:underline">
                <Lightning size={11} /> Mejorar
              </Link>
            )}
          </div>
        )}

        {/* Quick questions */}
        <Card className="p-4">
          <p className="text-xs font-semibold text-ink-400 uppercase tracking-wide mb-3">
            Preguntas frecuentes
          </p>
          <div className="space-y-0.5">
            {QUICK_QUESTIONS.map((q) => (
              <button
                key={q.text}
                onClick={() => send(q.text)}
                disabled={loading || isRateLimited}
                className="w-full flex items-start gap-2.5 text-left px-3 py-2.5 rounded-xl text-sm text-ink-700 hover:bg-surface-hover transition disabled:opacity-50"
              >
                <q.icon size={14} className="text-brand-400 flex-shrink-0 mt-0.5" />
                <span className="leading-snug">{q.text}</span>
              </button>
            ))}
          </div>
        </Card>

        {/* Escalate button */}
        <button
          onClick={escalate}
          className="w-full flex items-center justify-center gap-2 text-sm font-medium text-brand-600 border border-brand-200 hover:border-brand-400 hover:bg-brand-50 rounded-xl px-4 py-2.5 transition"
        >
          <EnvelopeSimple size={15} /> Escalar a soporte humano
        </button>

        <p className="text-xs text-center text-ink-400">
          soporte@jobper.co ·{" "}
          <Link to="/privacy" className="hover:underline">
            Privacidad
          </Link>
        </p>
      </div>

      {/* ── Right panel: chat ── */}
      <Card className="flex-1 flex flex-col min-h-[500px] lg:min-h-0 p-5">
        <div className="flex-1 overflow-y-auto space-y-3 pr-1 mb-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "bot" && (
                <div className="h-7 w-7 rounded-full bg-brand-100 flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                  <Robot size={14} className="text-brand-600" weight="duotone" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap leading-relaxed ${
                  m.role === "user"
                    ? "bg-brand-600 text-white rounded-br-sm"
                    : m.isSuggestions
                      ? "bg-surface-hover text-ink-400 border border-surface-border text-xs"
                      : "bg-surface-hover text-ink-800 rounded-bl-sm"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start items-center gap-2">
              <div className="h-7 w-7 rounded-full bg-brand-100 flex items-center justify-center">
                <ArrowsClockwise size={13} className="text-brand-600 animate-spin" />
              </div>
              <div className="bg-surface-hover rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1.5">
                <span
                  className="h-1.5 w-1.5 rounded-full bg-ink-300 animate-bounce"
                  style={{ animationDelay: "0ms" }}
                />
                <span
                  className="h-1.5 w-1.5 rounded-full bg-ink-300 animate-bounce"
                  style={{ animationDelay: "150ms" }}
                />
                <span
                  className="h-1.5 w-1.5 rounded-full bg-ink-300 animate-bounce"
                  style={{ animationDelay: "300ms" }}
                />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        {isRateLimited ? (
          <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
            <Lightning size={15} className="text-amber-600 flex-shrink-0" weight="fill" />
            <p className="text-sm text-amber-800 flex-1">
              Límite diario alcanzado.{" "}
              <Link to="/payments" className="font-semibold underline">
                Actualiza tu plan
              </Link>{" "}
              para mensajes ilimitados.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              className="flex-1"
              placeholder="Escribe tu pregunta... (Enter para enviar)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="h-10 w-10 flex-shrink-0 flex items-center justify-center rounded-xl bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
            >
              <PaperPlaneTilt size={16} weight="fill" />
            </button>
          </form>
        )}
      </Card>
    </div>
  );
}
