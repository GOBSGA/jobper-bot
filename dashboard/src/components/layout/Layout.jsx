import { useState } from "react";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import BottomNav from "./BottomNav";
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
        {/* Main: generous padding, bottom padding on mobile for BottomNav */}
        <main className="flex-1 px-5 py-6 pb-24 lg:px-8 lg:py-8 lg:pb-8 max-w-5xl mx-auto w-full">
          {children}
        </main>
      </div>
      <BottomNav />
      {showRenewal && <RenewalModal onClose={() => setShowRenewal(false)} />}
    </div>
  );
}
