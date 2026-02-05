export default function Logo({ size = 32, className = "" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      className={className}
      aria-label="Jobper logo"
    >
      <circle cx="24" cy="24" r="22" fill="#e85d2a" />
      <circle cx="18" cy="19" r="2.5" fill="white" />
      <circle cx="30" cy="19" r="2.5" fill="white" />
      <path
        d="M15 29 Q24 40 33 29"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}
