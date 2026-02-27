/**
 * Jobper logomark — clean geometric "J" lettermark.
 * Replaces the smiley face with a precise, premium badge.
 */
export default function Logo({ size = 32, className = "" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      className={className}
      aria-label="Jobper"
    >
      {/* Rounded square base */}
      <rect width="40" height="40" rx="10" fill="#4A58EE" />
      {/* J lettermark — vertical + tail */}
      <line x1="22" y1="9" x2="22" y2="27" stroke="white" strokeWidth="4" strokeLinecap="round" />
      <path
        d="M22 27 Q22 33 16 33 Q13 33 12 31"
        stroke="white"
        strokeWidth="4"
        strokeLinecap="round"
        fill="none"
      />
      {/* Serif cap — top bar */}
      <line x1="18" y1="9" x2="26" y2="9" stroke="white" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}
