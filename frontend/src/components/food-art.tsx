export function FoodArt({
  variant = 0,
  className = "",
}: {
  variant?: number;
  className?: string;
}) {
  const colors = [
    "#e5d1a8",
    "#e2ead2",
    "#f0d7bf",
    "#ddbd6a",
    "#dde0b0",
    "#e6c091",
  ];
  return (
    <svg
      className={className}
      viewBox="0 0 480 340"
      role="img"
      aria-label="Illustrated meal — sample menu artwork"
    >
      <ellipse cx="240" cy="300" rx="155" ry="15" fill="#152d2212" />
      <circle cx="240" cy="169" r="145" fill="#faf9f1" />
      <circle cx="240" cy="169" r="129" fill="#e9e7dc" />
      <circle cx="240" cy="169" r="117" fill={colors[variant % 6]} />
      <g fill="#548151">
        <ellipse
          cx="186"
          cy="122"
          rx="52"
          ry="25"
          transform="rotate(-35 186 122)"
        />
        <ellipse
          cx="283"
          cy="229"
          rx="58"
          ry="24"
          transform="rotate(-25 283 229)"
        />
        <ellipse cx="316" cy="124" rx="31" ry="25" />
      </g>
      <g fill={variant === 2 ? "#df8f64" : "#bc603e"}>
        <circle cx="164" cy="208" r="25" />
        <circle cx="301" cy="167" r="24" />
        <circle cx="240" cy="124" r="20" />
      </g>
      <g fill="#fff0bd">
        <circle cx="218" cy="206" r="11" />
        <circle cx="255" cy="177" r="12" />
        <circle cx="197" cy="159" r="9" />
        <circle cx="270" cy="103" r="10" />
        <circle cx="239" cy="247" r="9" />
      </g>
      <g stroke="#faf4d7" strokeWidth="3" strokeLinecap="round">
        <path d="m237 155 8 4m-65 75 8-3m115-21 8 4m-60-125 4 9" />
      </g>
    </svg>
  );
}
