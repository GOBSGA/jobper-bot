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

export default function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [searchParams] = useSearchParams();
  const referralCode = searchParams.get("ref");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const { submit, loading, error, setError } = useFormSubmit(async () => {
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
    navigate("/dashboard"); // PrivateRoute privacy gate handles acceptance
  });

  return (
    <AuthLayout title="Crear cuenta" subtitle="14 dias de prueba gratis">
        {referralCode && (
          <Alert variant="info">
            Te invitó un amigo — ¡ambos ganan 7 días extra!
          </Alert>
        )}

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
          <Button type="submit" className="w-full" disabled={loading}>
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

        <p className="text-center mt-4 text-xs text-gray-400">
          Al crear tu cuenta aceptas nuestros términos y condiciones.
        </p>
      </AuthLayout>
  );
}
