/**
 * Jobper logomark — B&W smiley with personality.
 * Horizontal pill eyes (happy-squinting) give it warmth and distinctiveness.
 * Near-black warm background, not cold #000.
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
      {/* Warm near-black rounded square */}
      <rect width="40" height="40" rx="11" fill="#111117" />

      {/* Eyes: horizontal pills — happy squinting, NOT generic circles */}
      <rect x="10" y="14" width="8" height="5" rx="2.5" fill="white" />
      <rect x="22" y="14" width="8" height="5" rx="2.5" fill="white" />

      {/* Smile: open confident arc */}
      <path
        d="M11 24 Q20 33 29 24"
        stroke="white"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}
