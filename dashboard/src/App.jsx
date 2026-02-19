import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Spinner from "./components/ui/Spinner";
import Layout from "./components/layout/Layout";

// Auth pages
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import Verify from "./pages/auth/Verify";
import ForgotPassword from "./pages/auth/ForgotPassword";
import ResetPassword from "./pages/auth/ResetPassword";
import Onboarding from "./pages/auth/Onboarding";
import OnboardingConversational from "./pages/auth/OnboardingConversational";

// App pages
import Dashboard from "./pages/dashboard/Dashboard";
import ContractSearch from "./pages/contracts/ContractSearch";
import ContractDetail from "./pages/contracts/ContractDetail";
import Favorites from "./pages/contracts/Favorites";
import Pipeline from "./pages/pipeline/Pipeline";
import Marketplace from "./pages/marketplace/Marketplace";
import Plans from "./pages/payments/Plans";
import Referrals from "./pages/payments/Referrals";
import Settings from "./pages/settings/Settings";
import Support from "./pages/support/Support";
import Admin from "./pages/admin/Admin";
import PaymentReview from "./pages/admin/PaymentReview";
import AdminUsers from "./pages/admin/AdminUsers";

// Public
import Landing from "./pages/public/Landing";
import Terms from "./pages/public/Terms";
import Privacy from "./pages/public/Privacy";

function PrivateRoute() {
  const { user, loading, serverError, refresh } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center"><Spinner className="h-8 w-8" /></div>;
  // Server error (5xx / network) while holding a valid token — show retry instead of login redirect
  if (!user && serverError) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 text-center px-4">
        <p className="text-gray-700 font-medium">No se pudo conectar con el servidor.</p>
        <p className="text-sm text-gray-500">Tu sesión sigue activa. Verifica tu conexión e intenta de nuevo.</p>
        <button
          onClick={() => refresh().catch(() => {})}
          className="px-5 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 transition"
        >
          Reintentar
        </button>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return <Layout><Outlet /></Layout>;
}

function AdminRoute() {
  const { user } = useAuth();
  if (!user?.is_admin) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

function PublicOnly() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route element={<PublicOnly />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>
      <Route path="/verify" element={<Verify />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/onboarding" element={<OnboardingConversational />} />
      <Route path="/onboarding/traditional" element={<Onboarding />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />

      {/* Private */}
      <Route element={<PrivateRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/contracts" element={<ContractSearch />} />
        <Route path="/contracts/:id" element={<ContractDetail />} />
        <Route path="/favorites" element={<Favorites />} />
        <Route path="/pipeline" element={<Pipeline />} />
        <Route path="/marketplace" element={<Marketplace />} />
        <Route path="/payments" element={<Plans />} />
        <Route path="/referrals" element={<Referrals />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/support" element={<Support />} />
        <Route path="/payment/result" element={<Plans />} />

        {/* Admin */}
        <Route element={<AdminRoute />}>
          <Route path="/admin" element={<Admin />} />
          <Route path="/admin/payments" element={<PaymentReview />} />
          <Route path="/admin/users" element={<AdminUsers />} />
        </Route>
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
