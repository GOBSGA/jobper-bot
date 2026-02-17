import { useState } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Logo from "../../components/ui/Logo";
import PrivacyPolicyModal from "../../components/PrivacyPolicyModal";
import { UserPlus, Eye, EyeOff } from "lucide-react";

export default function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [searchParams] = useSearchParams();
  const referralCode = searchParams.get("ref");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);

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
      await login(res);
      // Show privacy policy modal instead of navigating directly
      setShowPrivacyModal(true);
    } catch (err) {
      const msg = err.debug ? `${err.error} — ${err.debug}` : (err.error || "Error al crear la cuenta. Intenta de nuevo.");
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handlePrivacyAccept = () => {
    // Privacy policy accepted, proceed to onboarding
    setShowPrivacyModal(false);
    navigate("/onboarding");
  };

  const handlePrivacyReject = () => {
    // Privacy policy rejected, go to main page (contracts list)
    setShowPrivacyModal(false);
    navigate("/contracts");
  };

  return (
    <>
      {showPrivacyModal && (
        <PrivacyPolicyModal
          onAccept={handlePrivacyAccept}
          onReject={handlePrivacyReject}
        />
      )}

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

          {/* Error Alert */}
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

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
            <div className="relative">
              <Input
                label="Contraseña"
                id="register-password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                placeholder="Mínimo 6 caracteres"
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
            <Input
              label="Confirmar contraseña"
              id="register-confirm"
              name="confirm_password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              placeholder="Repite tu contraseña"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
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
    </>
  );
}
