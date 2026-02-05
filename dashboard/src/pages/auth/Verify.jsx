import { useEffect, useRef, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import Spinner from "../../components/ui/Spinner";

export default function Verify() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState("");
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    const token = params.get("token");
    const ref = params.get("ref");
    if (!token) { setError("Token inválido"); return; }

    api.post("/auth/verify", { token, referral_code: ref || undefined })
      .then((data) => {
        login(data);
        navigate(data.is_new ? "/onboarding" : "/dashboard", { replace: true });
      })
      .catch(() => setError("Link expirado o ya usado. Solicita otro."));
  }, []);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center hero-gradient px-4">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8 max-w-sm w-full text-center">
          <h1 className="text-xl font-bold text-gray-900 mb-2">Error de verificación</h1>
          <p className="text-sm text-gray-500 mb-6">{error}</p>
          <a href="/login" className="inline-block px-6 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition">Solicitar nuevo link</a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center hero-gradient">
      <div className="text-center">
        <Spinner className="h-8 w-8 mx-auto mb-4" />
        <p className="text-sm text-gray-500">Verificando...</p>
      </div>
    </div>
  );
}
