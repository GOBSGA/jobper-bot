import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import Spinner from "../../components/ui/Spinner";

/**
 * Landing page after Google OAuth redirect.
 * URL: /auth/google/callback?token=xxx&refresh=yyy&new=0|1
 * Stores tokens via AuthContext.login(), then fetches user profile and redirects.
 */
export default function GoogleCallback() {
  const [searchParams] = useSearchParams();
  const { login, refresh } = useAuth();
  const navigate = useNavigate();
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    const token = searchParams.get("token");
    const refreshToken = searchParams.get("refresh");
    const isNew = searchParams.get("new") === "1";
    const error = searchParams.get("error");

    if (error || !token || !refreshToken) {
      navigate("/login?error=google_failed", { replace: true });
      return;
    }

    login({ access_token: token, refresh_token: refreshToken })
      .then(() => refresh())  // load user data into state (login() alone doesn't set user for OAuth)
      .then(() => {
        navigate(isNew ? "/onboarding" : "/contracts", { replace: true });
      })
      .catch(() => {
        navigate("/login?error=google_failed", { replace: true });
      });
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-bg">
      <div className="text-center space-y-3">
        <Spinner className="h-8 w-8 mx-auto text-brand-600" />
        <p className="text-sm text-ink-400">Iniciando sesión con Google...</p>
      </div>
    </div>
  );
}
