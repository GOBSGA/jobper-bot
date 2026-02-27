import { useState } from "react";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import { useAuth } from "../../context/AuthContext";
import RenewalModal, { RenewalBanner } from "../ui/RenewalModal";

export default function Layout({ children }) {
  const { user, subscription } = useAuth();
  const [showRenewal, setShowRenewal] = useState(false);

  const isPaid = user?.plan && !["free", "trial"].includes(user.plan);
  const daysLeft = subscription?.days_remaining ?? null;
  const showBanner = isPaid && daysLeft !== null && daysLeft <= 3 && daysLeft > 0;

  return (
    <div className="flex min-h-screen bg-surface-bg">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        {showBanner && (
          <RenewalBanner daysLeft={daysLeft} onRenew={() => setShowRenewal(true)} />
        )}
        {/* Main: generous padding, pale uninterrupted expanse */}
        <main className="flex-1 px-5 py-6 lg:px-8 lg:py-8 max-w-5xl mx-auto w-full">
          {children}
        </main>
      </div>
      {showRenewal && <RenewalModal onClose={() => setShowRenewal(false)} />}
    </div>
  );
}
