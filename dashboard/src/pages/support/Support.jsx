import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import { MessageCircle, Send, Clock, Mail, Zap, Bot } from "lucide-react";

const SUPPORT_EMAIL = "soporte@jobper.co";

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
    const body = encodeURIComponent("Hola equipo de Jobper,\n\nNecesito ayuda con:\n\n[Describe tu problema aquí]\n\nGracias.");
    window.open(`mailto:${SUPPORT_EMAIL}?subject=${subject}&body=${body}`, "_blank");
  };

  const send = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await api.post("/support/chat", { question: q });

      if (res.messages_remaining != null) {
        setRemaining(res.messages_remaining);
      }

      const botMsg = { role: "bot", text: res.answer };
      setMessages((m) => [...m, botMsg]);

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

      if (res.rate_limited) {
        setRemaining(0);
      }
    } catch {
      setMessages((m) => [
        ...m,
        { role: "bot", text: "Ocurrió un error al procesar tu pregunta. Intenta de nuevo o escríbenos a soporte@jobper.co." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const isRateLimited = remaining === 0;

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="h-6 w-6 text-brand-600" />
          <h1 className="text-2xl font-bold text-gray-900">Asistente Jobper</h1>
        </div>
        <button
          onClick={escalate}
          className="flex items-center gap-2 text-sm text-brand-600 hover:text-brand-700 font-medium border border-brand-200 hover:border-brand-400 rounded-lg px-3 py-1.5 transition"
        >
          <Mail className="h-4 w-4" /> Escalar por correo
        </button>
      </div>

      {/* SLA */}
      <div className="flex items-start gap-3 bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 text-sm text-blue-800">
        <Clock className="h-4 w-4 mt-0.5 shrink-0 text-blue-500" />
        <span>
          El asistente está disponible 24/7. Para soporte humano respondemos a las{" "}
          <strong>6:00 AM</strong> y <strong>4:00 PM</strong> (hora Colombia, lun–vie).
        </span>
      </div>

      {/* Remaining messages */}
      {remaining !== null && (
        <div className={`flex items-center justify-between px-4 py-2 rounded-lg text-xs font-medium ${
          remaining <= 2 ? "bg-yellow-50 text-yellow-700 border border-yellow-200" : "bg-gray-50 text-gray-500"
        }`}>
          <span>{remaining > 0 ? `${remaining} consultas restantes hoy` : "Límite diario alcanzado"}</span>
          {remaining <= 2 && (
            <Link to="/payments" className="flex items-center gap-1 text-brand-600 hover:underline">
              <Zap className="h-3 w-3" /> Mejorar plan
            </Link>
          )}
        </div>
      )}

      {/* Chat */}
      <Card className="h-[480px] flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "bot" && (
                <div className="h-7 w-7 rounded-full bg-brand-100 flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                  <Bot className="h-4 w-4 text-brand-600" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap leading-relaxed ${
                  m.role === "user"
                    ? "bg-brand-600 text-white rounded-br-sm"
                    : m.isSuggestions
                    ? "bg-gray-50 text-gray-500 border border-gray-200 text-xs"
                    : "bg-gray-100 text-gray-800 rounded-bl-sm"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start items-center gap-2">
              <div className="h-7 w-7 rounded-full bg-brand-100 flex items-center justify-center">
                <Bot className="h-4 w-4 text-brand-600" />
              </div>
              <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-2.5 text-sm text-gray-400 flex items-center gap-1.5">
                <span className="animate-pulse">●</span>
                <span className="animate-pulse delay-100">●</span>
                <span className="animate-pulse delay-200">●</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={send} className="flex gap-2">
          <Input
            className="flex-1"
            placeholder={isRateLimited ? "Límite diario alcanzado — actualiza tu plan" : "Escribe tu pregunta..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isRateLimited}
          />
          <Button type="submit" disabled={loading || isRateLimited}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </Card>

      <p className="text-xs text-center text-gray-400">
        Soporte@jobper.co · Respuesta humana en horario comercial ·{" "}
        <Link to="/privacy" className="hover:underline">Privacidad</Link>
      </p>
    </div>
  );
}
