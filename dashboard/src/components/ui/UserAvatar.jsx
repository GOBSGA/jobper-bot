/**
 * Avatar — quiet monochrome. Gradient replaced with calm slate.
 * Initial letter is the identity signal; the circle is a neutral frame.
 */
export default function UserAvatar({ email, size = "sm" }) {
  const sizes = {
    sm: "h-7 w-7 text-xs",
    md: "h-8 w-8 text-xs",
    lg: "h-11 w-11 text-sm",
  };

  return (
    <div
      className={`${sizes[size]} rounded-xl bg-brand-50 text-brand-600 border border-brand-100 flex items-center justify-center font-semibold flex-shrink-0 tracking-snug`}
    >
      {email?.[0]?.toUpperCase() || "?"}
    </div>
  );
}
