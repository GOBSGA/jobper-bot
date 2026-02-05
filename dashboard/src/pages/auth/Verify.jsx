import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import Spinner from "../../components/ui/Spinner";

// Module-level flag to prevent double verification in React 18 StrictMode
// and from email link scanners (Gmail, Outlook Safe Links)
const verifiedTokens = new Set();

export default function Verify() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState("");
  const [verifying, setVerifying] = useState(true);

  useEffect(() => {
    const token = params.get("token");
    const ref = params.get("ref");

    if (!token) {
      setError("Token inválido");
      setVerifying(false);
      return;
    }

    // Prevent double-verification (React 18 StrictMode, email scanners, etc.)
    if (verifiedTokens.has(token)) {
      // Token is being processed, wait for result
      return;
    }
    verifiedTokens.add(token);

    api.post("/auth/verify", { token, referral_code: ref || undefined })
      .then((data) => {
        login(data);
        navigate(data.is_new ? "/onboarding" : "/dashboard", { replace: true });
      })
      .catch((err) => {
        // Remove from set so user can retry with a new link
        verifiedTokens.delete(token);
        // Show specific error from API if available
        const apiError = err?.response?.data?.error || err?.message;
        setError(apiError || "Error verificando el enlace. Solicita uno nuevo.");
        setVerifying(false);
      });
  }, [params, login, navigate]);

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
