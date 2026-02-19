import Logo from "../ui/Logo";

export default function AuthLayout({ children, title, subtitle }) {
  return (
    <div className="min-h-screen flex items-center justify-center hero-gradient px-4">
      <div className="w-full max-w-sm">
        <div className="bg-white rounded-2xl shadow-xl shadow-gray-200/50 border border-gray-100 p-8">
          <div className="text-center mb-6">
            <Logo size={56} className="mx-auto mb-5" />
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">{title}</h1>
            {subtitle && <p className="mt-2 text-sm text-gray-500">{subtitle}</p>}
          </div>
          {children}
        </div>
        <p className="text-center mt-6 text-xs text-gray-400">
          &copy; {new Date().getFullYear()} Jobper — soporte@jobper.co
        </p>
      </div>
    </div>
  );
}
