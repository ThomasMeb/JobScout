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
        {/* Magnifying glass body */}
        <circle cx="22" cy="22" r="14" stroke="#2563EB" strokeWidth="3.5" fill="#EFF6FF" />
        {/* Radar arcs inside */}
        <path d="M22 14a8 8 0 0 1 8 8" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
        <path d="M22 18a4 4 0 0 1 4 4" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" opacity="0.7" />
        {/* Center dot */}
        <circle cx="22" cy="22" r="2" fill="#2563EB" />
        {/* Handle */}
        <line x1="33" y1="33" x2="43" y2="43" stroke="#1E40AF" strokeWidth="4" strokeLinecap="round" />
      </svg>
      {showText && (
        <span className={text}>
          <span className="text-blue-600">Job</span>
          <span className="text-gray-900 dark:text-white">Scout</span>
        </span>
      )}
    </span>
  );
}
