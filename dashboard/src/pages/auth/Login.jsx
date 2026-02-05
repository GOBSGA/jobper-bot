import { useState } from "react";
import { api } from "../../lib/api";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Logo from "../../components/ui/Logo";
import { Mail, ArrowLeft } from "lucide-react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/login", { email });
      setSent(true);
    } catch (err) {
      setError(err.error || "Error enviando el link. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center hero-gradient px-4">
      <div className="w-full max-w-sm">
        <div className="bg-white rounded-2xl shadow-xl shadow-gray-200/50 border border-gray-100 p-8">
          <div className="text-center mb-8">
            <Logo size={56} className="mx-auto mb-5" />
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Bienvenido a Jobper</h1>
            <p className="mt-2 text-sm text-gray-500">CRM de contratos para Colombia</p>
          </div>

          {sent ? (
            <div className="rounded-xl bg-green-50 border border-green-200 p-6 text-center">
              <div className="mx-auto w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-4">
                <Mail className="h-6 w-6 text-green-600" />
              </div>
              <h2 className="font-semibold text-green-800">Revisa tu email</h2>
              <p className="mt-2 text-sm text-green-700 leading-relaxed">
                Enviamos un link mágico a <strong>{email}</strong>. Haz clic para iniciar sesión.
              </p>
              <button onClick={() => setSent(false)} className="mt-5 inline-flex items-center gap-1 text-sm text-brand-600 hover:underline">
                <ArrowLeft className="h-3.5 w-3.5" /> Usar otro email
              </button>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-5">
              <Input
                label="Email"
                type="email"
                placeholder="tu@empresa.co"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                error={error}
                required
              />
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Enviando..." : "Enviar link mágico"}
              </Button>
              <p className="text-xs text-gray-400 text-center leading-relaxed">
                Sin contraseñas. Te enviamos un link seguro a tu email.
              </p>
            </form>
          )}
        </div>

        <p className="text-center mt-6 text-xs text-gray-400">
          &copy; {new Date().getFullYear()} Jobper — soporte@jobper.co
        </p>
      </div>
    </div>
  );
}
