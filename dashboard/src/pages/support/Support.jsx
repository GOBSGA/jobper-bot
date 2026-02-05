import { useState } from "react";
import { api } from "../../lib/api";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import { MessageCircle, Send } from "lucide-react";

export default function Support() {
  const [messages, setMessages] = useState([
    { role: "bot", text: "¡Hola! Soy el asistente de Jobper. ¿En qué te puedo ayudar?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

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
        ...(res.suggestions ? [{ role: "bot", text: `Preguntas sugeridas:\n${res.suggestions.map((s) => `• ${s}`).join("\n")}` }] : []),
      ]);
    } catch {
      setMessages((m) => [...m, { role: "bot", text: "Error al procesar tu pregunta. Intenta de nuevo." }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-2">
        <MessageCircle className="h-6 w-6 text-brand-600" />
        <h1 className="text-2xl font-bold text-gray-900">Soporte</h1>
      </div>

      <Card className="h-[500px] flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-3 mb-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-xl px-4 py-2 text-sm whitespace-pre-wrap ${
                m.role === "user" ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-800"
              }`}>
                {m.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-xl px-4 py-2 text-sm text-gray-400">Escribiendo...</div>
            </div>
          )}
        </div>
        <form onSubmit={send} className="flex gap-2">
          <Input className="flex-1" placeholder="Escribe tu pregunta..." value={input} onChange={(e) => setInput(e.target.value)} />
          <Button type="submit" disabled={loading}><Send className="h-4 w-4" /></Button>
        </form>
      </Card>
    </div>
  );
}
