import { useState } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Alert from "../../components/ui/Alert";
import PasswordInput from "../../components/ui/PasswordInput";
import AuthLayout from "../../components/auth/AuthLayout";
import { useFormSubmit } from "../../hooks/useFormSubmit";
import { UserPlus } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

export default function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [searchParams] = useSearchParams();
  const referralCode = searchParams.get("ref");

  const googleAuthUrl = referralCode
    ? `${API_BASE}/auth/google?ref=${encodeURIComponent(referralCode)}`
    : `${API_BASE}/auth/google`;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const { submit, loading, error, setError } = useFormSubmit(async () => {
    if (!acceptedTerms) {
      setError("Debes aceptar los términos y la política de privacidad para continuar");
      return;
    }
    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }
    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres");
      return;
    }

    const res = await api.post("/auth/register", {
      email,
      password,
      referral_code: referralCode || undefined,
    });
    await login(res);
    navigate(res.is_new ? "/onboarding" : "/dashboard");
  });

  return (
    <AuthLayout title="Crear cuenta" subtitle="14 días de prueba gratis">
        {referralCode && (
          <Alert variant="info">
            Te invitó un amigo — ¡ambos ganan 7 días extra!
          </Alert>
        )}

        {/* Google button */}
        <a
          href={googleAuthUrl}
          className="flex w-full items-center justify-center gap-3 rounded-xl border border-surface-border bg-white px-4 py-2.5 text-sm font-medium text-ink-900 shadow-sm hover:bg-surface-hover transition-colors"
        >
          <svg width="18" height="18" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            <path fill="none" d="M0 0h48v48H0z"/>
          </svg>
          Continuar con Google
        </a>

        <div className="flex items-center gap-3 my-5">
          <div className="flex-1 h-px bg-surface-border" />
          <span className="text-xs text-ink-400">o crea una cuenta con email</span>
          <div className="flex-1 h-px bg-surface-border" />
        </div>

        {error && <Alert variant="error">{error}</Alert>}

        <form onSubmit={submit} className="space-y-4">
          <Input
            label="Email"
            id="register-email"
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
            id="register-password"
            name="password"
            placeholder="Mínimo 6 caracteres"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
          <PasswordInput
            label="Confirmar contraseña"
            id="register-confirm"
            name="confirm_password"
            placeholder="Repite tu contraseña"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={acceptedTerms}
              onChange={(e) => setAcceptedTerms(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500 flex-shrink-0"
            />
            <span className="text-sm text-gray-600">
              He leído y acepto los{" "}
              <Link to="/terms" target="_blank" className="text-brand-600 hover:underline font-medium">
                Términos y Condiciones
              </Link>{" "}
              y la{" "}
              <Link to="/privacy" target="_blank" className="text-brand-600 hover:underline font-medium">
                Política de Privacidad
              </Link>
            </span>
          </label>
          <Button type="submit" className="w-full" disabled={loading || !acceptedTerms}>
            {loading ? (
              "Creando cuenta..."
            ) : (
              <>
                <UserPlus className="h-4 w-4 mr-2" />
                Crear cuenta gratis
              </>
            )}
          </Button>
          <p className="text-sm text-center text-gray-500">
            ¿Ya tienes cuenta?{" "}
            <Link to="/login" className="text-brand-600 hover:underline font-medium">
              Inicia sesión
            </Link>
          </p>
        </form>
      </AuthLayout>
  );
}
