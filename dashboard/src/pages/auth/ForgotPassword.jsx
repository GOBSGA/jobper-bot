import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Logo from "../../components/ui/Logo";
import { Mail, ArrowLeft, CheckCircle } from "lucide-react";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/forgot-password", { email });
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
          <div className="text-center mb-6">
            <Logo size={56} className="mx-auto mb-5" />
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
              {sent ? "Revisa tu email" : "Recuperar contraseña"}
            </h1>
            <p className="mt-2 text-sm text-gray-500">
              {sent
                ? "Te enviamos un link de acceso"
                : "Te enviaremos un link para acceder sin contraseña"
              }
            </p>
          </div>

          {sent ? (
            <div className="rounded-xl bg-green-50 border border-green-200 p-6 text-center">
              <div className="mx-auto w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-4">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <p className="text-sm text-green-700 leading-relaxed">
                Enviamos un link mágico a <strong>{email}</strong>. Haz clic en el link para acceder sin contraseña.
              </p>
              <Link
                to="/login"
                className="mt-5 inline-flex items-center gap-1 text-sm text-brand-600 hover:underline"
              >
                <ArrowLeft className="h-3.5 w-3.5" /> Volver al login
              </Link>
            </div>
          ) : (
            <>
              {error && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <form onSubmit={submit} className="space-y-5">
                <Input
                  label="Email"
                  type="email"
                  placeholder="tu@empresa.co"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Enviando..." : (
                    <>
                      <Mail className="h-4 w-4 mr-2" />
                      Enviar link de recuperación
                    </>
                  )}
                </Button>
                <Link
                  to="/login"
                  className="block text-center text-sm text-gray-500 hover:text-gray-700"
                >
                  <ArrowLeft className="h-3.5 w-3.5 inline mr-1" />
                  Volver al login
                </Link>
              </form>
            </>
          )}
        </div>

        <p className="text-center mt-6 text-xs text-gray-400">
          &copy; {new Date().getFullYear()} Jobper — soporte@jobper.co
        </p>
      </div>
    </div>
  );
}
