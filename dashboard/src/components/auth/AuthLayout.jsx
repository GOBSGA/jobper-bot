import Logo from "../ui/Logo";

export default function AuthLayout({ children, title, subtitle }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-bg px-4">
      <div className="w-full max-w-sm">
        <div className="bg-white rounded-2xl border border-surface-border p-8">
          <div className="text-center mb-7">
            <div className="flex justify-center mb-5">
              <Logo size={48} />
            </div>
            <h1 className="text-lg font-bold text-ink-900 tracking-tighter">{title}</h1>
            {subtitle && (
              <p className="mt-1.5 text-sm text-ink-400 leading-relaxed">{subtitle}</p>
            )}
          </div>
          {children}
        </div>
        <p className="text-center mt-5 text-2xs text-ink-400">
          &copy; {new Date().getFullYear()} Jobper &mdash; soporte@jobper.co
        </p>
      </div>
    </div>
  );
}
