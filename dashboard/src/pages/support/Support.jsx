import { useState, useRef, useEffect } from "react";
import { api } from "../../lib/api";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import { MessageCircle, Send, Clock, Mail } from "lucide-react";

const SUPPORT_EMAIL = "soporte@jobper.co";

const SLA_MESSAGE =
  "Revisamos los tickets y respondemos correos a las **6:00 AM** y a las **4:00 PM** (hora Colombia, lunes a viernes). " +
  "Si tu consulta es urgente y el bot no puede ayudarte, usa el botón de correo de abajo para escalar al equipo. 📩";

export default function Support() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "¡Hola! Soy el asistente de Jobper. ¿En qué te puedo ayudar?",
    },
    { role: "bot", text: SLA_MESSAGE },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const q = input;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await api.post("/support/chat", { question: q });
      setMessages((m) => [
        ...m,
        { role: "bot", text: res.answer },
        ...(res.suggestions
          ? [
              {
                role: "bot",
                text: `Preguntas sugeridas:\n${res.suggestions.map((s) => `• ${s}`).join("\n")}`,
              },
            ]
          : []),
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "bot",
          text: "Error al procesar tu pregunta. Intenta de nuevo.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const escalateToEmail = () => {
    const subject = encodeURIComponent("Soporte Jobper — Consulta urgente");
    const body = encodeURIComponent(
      "Hola equipo de Jobper,\n\nNecesito ayuda con lo siguiente:\n\n[Describe tu problema aquí]\n\nGracias."
    );
    window.open(`mailto:${SUPPORT_EMAIL}?subject=${subject}&body=${body}`, "_blank");
  };

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageCircle className="h-6 w-6 text-brand-600" />
          <h1 className="text-2xl font-bold text-gray-900">Soporte</h1>
        </div>
        <button
          onClick={escalateToEmail}
          className="flex items-center gap-2 text-sm text-brand-600 hover:text-brand-700 font-medium border border-brand-200 hover:border-brand-400 rounded-lg px-3 py-1.5 transition"
        >
          <Mail className="h-4 w-4" />
          Escalar por correo
        </button>
      </div>

      {/* SLA info banner */}
      <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-800">
        <Clock className="h-4 w-4 mt-0.5 shrink-0 text-blue-500" />
        <span>
          Respondemos a las <strong>6:00 AM</strong> y <strong>4:00 PM</strong>{" "}
          (hora Colombia, lun–vie). Para urgencias usa el botón{" "}
          <em>Escalar por correo</em>.
        </span>
      </div>

      <Card className="h-[460px] flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-xl px-4 py-2 text-sm whitespace-pre-wrap ${
                  m.role === "user"
                    ? "bg-brand-600 text-white"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-xl px-4 py-2 text-sm text-gray-400">
                Escribiendo...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
        <form onSubmit={send} className="flex gap-2">
          <Input
            className="flex-1"
            placeholder="Escribe tu pregunta..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <Button type="submit" disabled={loading}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </Card>
    </div>
  );
}
