import { useState, useEffect } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Alert from "../../components/ui/Alert";
import PasswordInput from "../../components/ui/PasswordInput";
import AuthLayout from "../../components/auth/AuthLayout";
import SuccessCard from "../../components/auth/SuccessCard";
import { useFormSubmit } from "../../hooks/useFormSubmit";
import { Lock, ArrowLeft, CheckCircle } from "lucide-react";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [done, setDone] = useState(false);

  const { submit, loading, error, setError } = useFormSubmit(async () => {
    if (password !== confirm) {
      setError("Las contraseñas no coinciden");
      return;
    }
    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres");
      return;
    }
    const res = await api.post("/auth/reset-password", { token, new_password: password });
    await login(res);
    setDone(true);
    setTimeout(() => navigate("/contracts"), 2000);
  });

  useEffect(() => {
    if (!token) navigate("/forgot-password", { replace: true });
  }, [token, navigate]);

  if (done) {
    return (
      <AuthLayout title="Nueva contraseña">
        <SuccessCard
          icon={CheckCircle}
          title="Contraseña actualizada"
          message="Redirigiendo a tu cuenta..."
        />
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Nueva contraseña"
      subtitle="Elige una contraseña segura para tu cuenta"
    >
      {error && <Alert variant="error">{error}</Alert>}

      <form onSubmit={submit} className="space-y-4">
        <PasswordInput
          label="Nueva contraseña"
          placeholder="Mínimo 6 caracteres"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={6}
          autoComplete="new-password"
        />
        <Input
          label="Confirmar contraseña"
          type="password"
          placeholder="Repite la contraseña"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
          autoComplete="new-password"
        />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Guardando..." : (
            <span className="flex items-center justify-center gap-2">
              <Lock className="h-4 w-4" />
              Guardar nueva contraseña
            </span>
          )}
        </Button>
      </form>

      <Link
        to="/login"
        className="mt-4 block text-center text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-3.5 w-3.5 inline mr-1" />
        Volver al login
      </Link>
    </AuthLayout>
  );
}
