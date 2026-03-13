interface LogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
  className?: string;
}

const sizes = {
  sm: { icon: 24, text: "text-lg" },
  md: { icon: 32, text: "text-xl" },
  lg: { icon: 48, text: "text-3xl" },
};

export default function Logo({ size = "md", showText = true, className = "" }: LogoProps) {
  const { icon, text } = sizes[size];

  return (
    <span className={`inline-flex items-center gap-2 font-bold ${className}`}>
      <svg
        width={icon}
        height={icon}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="logo-amber" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FBBF24" />
            <stop offset="100%" stopColor="#D97706" />
          </linearGradient>
        </defs>
        {/* Magnifying glass body */}
        <circle cx="22" cy="22" r="14" stroke="url(#logo-amber)" strokeWidth="3.5" fill="#F59E0B0D" />
        {/* Radar arcs inside */}
        <path d="M22 14a8 8 0 0 1 8 8" stroke="#FBBF24" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
        <path d="M22 18a4 4 0 0 1 4 4" stroke="#FBBF24" strokeWidth="2" strokeLinecap="round" opacity="0.7" />
        {/* Center dot */}
        <circle cx="22" cy="22" r="2" fill="#F59E0B" />
        {/* Handle */}
        <line x1="33" y1="33" x2="43" y2="43" stroke="#D97706" strokeWidth="4" strokeLinecap="round" />
      </svg>
      {showText && (
        <span className={text}>
          <span className="text-amber-bright">Job</span>
          <span className="text-text-primary">Scout</span>
        </span>
      )}
    </span>
  );
}
