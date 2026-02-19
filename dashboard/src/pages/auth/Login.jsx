import { useState } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Alert from "../../components/ui/Alert";
import PasswordInput from "../../components/ui/PasswordInput";
import AuthLayout from "../../components/auth/AuthLayout";
import SuccessCard from "../../components/auth/SuccessCard";
import { useFormSubmit } from "../../hooks/useFormSubmit";
import { Mail, ArrowLeft, Lock } from "lucide-react";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [searchParams] = useSearchParams();
  const referralCode = searchParams.get("ref");

  const [mode, setMode] = useState("password"); // "password" or "magic"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [sent, setSent] = useState(false);

  const { submit: submitPassword, loading: loadingPw, error: errorPw } = useFormSubmit(async () => {
    const res = await api.post("/auth/login-password", { email, password });
    await login(res);
    navigate("/contracts");
  });

  const { submit: submitMagic, loading: loadingMagic, error: errorMagic } = useFormSubmit(async () => {
    await api.post("/auth/login", { email });
    setSent(true);
  });

  const loading = loadingPw || loadingMagic;
  const error = errorPw || errorMagic;

  if (sent) {
    return (
      <AuthLayout title="Revisa tu email">
        <SuccessCard
          icon={Mail}
          title="Revisa tu email"
          message={
            <>
              Enviamos un link mágico a <strong>{email}</strong>. Haz clic para iniciar sesión.
            </>
          }
          action={
            <button
              onClick={() => setSent(false)}
              className="mt-5 inline-flex items-center gap-1 text-sm text-brand-600 hover:underline"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Usar otro email
            </button>
          }
        />
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Iniciar sesión" subtitle="CRM de contratos para Colombia">
      {/* Mode Toggle */}
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

      {error && <Alert variant="error">{error}</Alert>}

      {mode === "password" ? (
        <form onSubmit={submitPassword} className="space-y-4">
          <Input
            label="Email"
            id="login-email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="tu@empresa.co"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <PasswordInput
            label="Contraseña"
            id="login-password"
            name="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
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
            <Link to={referralCode ? `/register?ref=${referralCode}` : "/register"} className="text-brand-600 hover:underline font-medium">
              Regístrate
            </Link>
          </p>
        </form>
      ) : (
        <form onSubmit={submitMagic} className="space-y-5">
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
    </AuthLayout>
  );
}
