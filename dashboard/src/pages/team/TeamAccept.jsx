import { useEffect, useState } from "react";
import { useParams, useSearchParams, Link } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import Spinner from "../../components/ui/Spinner";
import { CheckCircle, XCircle, UsersThree } from "@phosphor-icons/react";
import Logo from "../../components/ui/Logo";

export default function TeamAccept() {
  const { token } = useParams();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();

  const success = searchParams.get("success") === "1";
  const errorParam = searchParams.get("error");
  const ownerEmail = searchParams.get("owner_email");

  const [status, setStatus] = useState(
    success ? "success" : errorParam ? "error" : token ? "loading" : "error"
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token || success || errorParam) return;

    // If we have a token in the path, redirect to the backend acceptance endpoint
    window.location.href = `/api/team/accept/${token}`;
  }, [token, success, errorParam]);

  const errorMessages = {
    invalid_invite: "Este enlace de invitación no es válido o ya fue usado.",
    expired: "Este enlace de invitación ha expirado. Solicita un nuevo enlace al administrador del equipo.",
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <Logo size={32} />
          <span className="text-lg font-bold tracking-tighter text-ink-900">Jobper</span>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl border border-surface-border p-8 text-center shadow-sm">
          {status === "loading" && (
            <>
              <div className="flex justify-center mb-4">
                <Spinner className="h-8 w-8" />
              </div>
              <p className="text-sm text-ink-600">Procesando invitación...</p>
            </>
          )}

          {status === "success" && (
            <>
              <div className="flex justify-center mb-4">
                <div className="w-16 h-16 rounded-2xl bg-green-50 flex items-center justify-center">
                  <CheckCircle size={32} className="text-green-500" weight="duotone" />
                </div>
              </div>
              <h1 className="text-xl font-bold text-ink-900 mb-2">¡Bienvenido al equipo!</h1>
              {ownerEmail && (
                <p className="text-sm text-ink-600 mb-1">
                  Ahora eres parte del equipo de <strong>{ownerEmail}</strong>.
                </p>
              )}
              <p className="text-sm text-ink-400 mb-6">
                Ya tienes acceso al pipeline compartido y podrás colaborar con tu equipo.
              </p>

              <div className="flex flex-col gap-3">
                {user ? (
                  <Link
                    to="/team"
                    className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 transition-colors"
                  >
                    <UsersThree size={16} />
                    Ver el equipo
                  </Link>
                ) : (
                  <>
                    <Link
                      to="/login"
                      className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 transition-colors"
                    >
                      Iniciar sesión
                    </Link>
                    <Link
                      to="/register"
                      className="inline-flex items-center justify-center px-5 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-ink-700 hover:bg-surface-hover transition-colors"
                    >
                      Crear cuenta
                    </Link>
                  </>
                )}
              </div>
            </>
          )}

          {(status === "error" || errorParam) && (
            <>
              <div className="flex justify-center mb-4">
                <div className="w-16 h-16 rounded-2xl bg-red-50 flex items-center justify-center">
                  <XCircle size={32} className="text-red-400" weight="duotone" />
                </div>
              </div>
              <h1 className="text-xl font-bold text-ink-900 mb-2">Enlace inválido</h1>
              <p className="text-sm text-ink-600 mb-6">
                {errorMessages[errorParam] || "Este enlace de invitación no es válido o ha expirado."}
              </p>

              <Link
                to="/"
                className="inline-flex items-center justify-center px-5 py-2.5 rounded-xl bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 transition-colors"
              >
                Ir a Jobper
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
