export default function UserAvatar({ email, size = "sm" }) {
  const sizes = {
    sm: "h-7 w-7 text-xs",
    md: "h-9 w-9 text-sm",
    lg: "h-12 w-12 text-base",
  };

  return (
    <div className={`${sizes[size]} rounded-full bg-gradient-to-br from-brand-400 to-purple-400 text-white flex items-center justify-center font-bold flex-shrink-0`}>
      {email?.[0]?.toUpperCase() || "?"}
    </div>
  );
}
