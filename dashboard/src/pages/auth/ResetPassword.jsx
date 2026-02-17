import { useState, useEffect } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Logo from "../../components/ui/Logo";
import { Lock, Eye, EyeOff, ArrowLeft, CheckCircle } from "lucide-react";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!token) navigate("/forgot-password", { replace: true });
  }, [token, navigate]);

  const submit = async (e) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Las contraseñas no coinciden");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await api.post("/auth/reset-password", { token, new_password: password });
      await login(res);
      setDone(true);
      setTimeout(() => navigate("/contracts"), 2000);
    } catch (err) {
      setError(err.error || "El enlace expiró o es inválido. Solicita uno nuevo.");
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
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Nueva contraseña</h1>
            <p className="mt-2 text-sm text-gray-500">Elige una contraseña segura para tu cuenta</p>
          </div>

          {done ? (
            <div className="rounded-xl bg-green-50 border border-green-200 p-6 text-center">
              <CheckCircle className="h-10 w-10 text-green-600 mx-auto mb-3" />
              <h2 className="font-semibold text-green-800">Contraseña actualizada</h2>
              <p className="mt-2 text-sm text-green-700">Redirigiendo a tu cuenta...</p>
            </div>
          ) : (
            <>
              {error && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}
              <form onSubmit={submit} className="space-y-4">
                <div className="relative">
                  <Input
                    label="Nueva contraseña"
                    type={showPw ? "text" : "password"}
                    placeholder="Mínimo 6 caracteres"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-[34px] text-gray-400 hover:text-gray-600"
                  >
                    {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <Input
                  label="Confirmar contraseña"
                  type="password"
                  placeholder="Repite la contraseña"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
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
