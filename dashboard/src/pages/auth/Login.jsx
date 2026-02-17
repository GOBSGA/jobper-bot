import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Logo from "../../components/ui/Logo";
import { Mail, ArrowLeft, Lock, Eye, EyeOff } from "lucide-react";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [mode, setMode] = useState("password"); // "password" or "magic"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submitPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.post("/auth/login-password", { email, password });
      await login(res);
      navigate("/contracts");
    } catch (err) {
      // Show the debug field from server if available (helps diagnose backend errors)
      const msg = err.debug ? `${err.error} — ${err.debug}` : (err.error || "Correo o contraseña incorrectos");
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const submitMagicLink = async (e) => {
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
          <div className="text-center mb-6">
            <Logo size={56} className="mx-auto mb-5" />
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Iniciar sesión</h1>
            <p className="mt-2 text-sm text-gray-500">CRM de contratos para Colombia</p>
          </div>

          {/* Mode Toggle */}
          {!sent && (
            <div className="flex rounded-lg bg-gray-100 p-1 mb-6">
              <button
                type="button"
                onClick={() => setMode("password")}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition ${
                  mode === "password"
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                <Lock className="h-4 w-4 inline mr-1.5 -mt-0.5" />
                Contraseña
              </button>
              <button
                type="button"
                onClick={() => setMode("magic")}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition ${
                  mode === "magic"
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                <Mail className="h-4 w-4 inline mr-1.5 -mt-0.5" />
                Magic Link
              </button>
            </div>
          )}

          {/* Error Alert */}
          {error && !sent && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

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
          ) : mode === "password" ? (
            <form onSubmit={submitPassword} className="space-y-4">
              <Input
                label="Email"
                type="email"
                placeholder="tu@empresa.co"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <div className="relative">
                <Input
                  label="Contraseña"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-[34px] text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <div className="text-right -mt-1 mb-3">
                <Link to="/forgot-password" className="text-xs text-gray-500 hover:text-brand-600">
                  ¿Olvidaste tu contraseña?
                </Link>
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Entrando..." : "Iniciar sesión"}
              </Button>
              <p className="text-sm text-center text-gray-500">
                ¿No tienes cuenta?{" "}
                <Link to="/register" className="text-brand-600 hover:underline font-medium">
                  Regístrate
                </Link>
              </p>
            </form>
          ) : (
            <form onSubmit={submitMagicLink} className="space-y-5">
              <Input
                label="Email"
                type="email"
                placeholder="tu@empresa.co"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
