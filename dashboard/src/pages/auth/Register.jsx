import { useState } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Logo from "../../components/ui/Logo";
import { UserPlus } from "lucide-react";

export default function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [searchParams] = useSearchParams();
  const referralCode = searchParams.get("ref");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }

    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres");
      return;
    }

    setLoading(true);
    try {
      const res = await api.post("/auth/register", {
        email,
        password,
        referral_code: referralCode || undefined,
      });
      login(res.access_token, res.refresh_token, res.user);
      navigate("/onboarding");
    } catch (err) {
      setError(err.error || "Error al crear la cuenta. Intenta de nuevo.");
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
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Crear cuenta</h1>
            <p className="mt-2 text-sm text-gray-500">14 días de prueba gratis</p>
          </div>

          {referralCode && (
            <div className="mb-4 rounded-lg bg-brand-50 border border-brand-200 p-3 text-center">
              <p className="text-sm text-brand-700">
                Te invitó un amigo — ¡ambos ganan 7 días extra!
              </p>
            </div>
          )}

          <form onSubmit={submit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="tu@empresa.co"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              label="Contraseña"
              type="password"
              placeholder="Mínimo 6 caracteres"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Input
              label="Confirmar contraseña"
              type="password"
              placeholder="Repite tu contraseña"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              error={error}
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
        </div>

        <p className="text-center mt-6 text-xs text-gray-400">
          Al crear tu cuenta aceptas nuestros términos y condiciones.
        </p>
      </div>
    </div>
  );
}
