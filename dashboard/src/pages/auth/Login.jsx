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
import { EnvelopeSimple, ArrowLeft, Lock } from "@phosphor-icons/react";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [searchParams] = useSearchParams();
  const referralCode = searchParams.get("ref");
  const urlError = searchParams.get("error");

  const [mode, setMode] = useState("password"); // "password" | "magic"
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

  const googleAuthUrl = referralCode
    ? `${API_BASE}/auth/google?ref=${encodeURIComponent(referralCode)}`
    : `${API_BASE}/auth/google`;

  if (sent) {
    return (
      <AuthLayout title="Revisa tu email">
        <SuccessCard
          icon={EnvelopeSimple}
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
              <ArrowLeft size={14} /> Usar otro email
            </button>
          }
        />
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Iniciar sesión" subtitle="CRM de contratos para Colombia">
      {/* Error from OAuth redirect */}
      {urlError && (
        <Alert variant="error" className="mb-4">
          {urlError === "google_cancelled"
            ? "Cancelaste el acceso con Google."
            : "No se pudo iniciar sesión con Google. Intenta de nuevo."}
        </Alert>
      )}

      {/* Google button */}
      <a
        href={googleAuthUrl}
        className="flex w-full items-center justify-center gap-3 rounded-xl border border-surface-border bg-white px-4 py-2.5 text-sm font-medium text-ink-900 shadow-sm hover:bg-surface-hover transition-colors"
      >
        {/* Google G logo — inline SVG, no extra dependency */}
        <svg width="18" height="18" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
          <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
          <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
          <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
          <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
          <path fill="none" d="M0 0h48v48H0z"/>
        </svg>
        Continuar con Google
      </a>

      {/* Divider */}
      <div className="flex items-center gap-3 my-5">
        <div className="flex-1 h-px bg-surface-border" />
        <span className="text-xs text-ink-400">o usa tu email</span>
        <div className="flex-1 h-px bg-surface-border" />
      </div>

      {/* Mode toggle */}
      <div className="flex rounded-xl bg-surface-hover p-1 mb-5">
        <button
          type="button"
          onClick={() => setMode("password")}
          className={`flex-1 py-2 text-sm font-medium rounded-lg transition ${
            mode === "password"
              ? "bg-white text-ink-900 shadow-sm"
              : "text-ink-400 hover:text-ink-600"
          }`}
        >
          <Lock size={13} className="inline mr-1.5 -mt-0.5" weight={mode === "password" ? "bold" : "regular"} />
          Contraseña
        </button>
        <button
          type="button"
          onClick={() => setMode("magic")}
          className={`flex-1 py-2 text-sm font-medium rounded-lg transition ${
            mode === "magic"
              ? "bg-white text-ink-900 shadow-sm"
              : "text-ink-400 hover:text-ink-600"
          }`}
        >
          <EnvelopeSimple size={13} className="inline mr-1.5 -mt-0.5" weight={mode === "magic" ? "bold" : "regular"} />
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
            <Link to="/forgot-password" className="text-xs text-ink-400 hover:text-brand-600">
              ¿Olvidaste tu contraseña?
            </Link>
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Entrando..." : "Iniciar sesión"}
          </Button>
          <p className="text-sm text-center text-ink-400">
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
          <p className="text-xs text-ink-400 text-center leading-relaxed">
            Sin contraseñas. Te enviamos un link seguro a tu email.
          </p>
        </form>
      )}
    </AuthLayout>
  );
}
