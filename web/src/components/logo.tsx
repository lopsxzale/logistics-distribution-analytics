/** Marca do site: mesmo desenho do favicon (src/app/icon.svg). Gota de combustível com tendência. */
export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden className="shrink-0">
      <defs>
        <linearGradient id="logo-bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#4ADE80" />
          <stop offset="1" stopColor="#16A34A" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="16" fill="url(#logo-bg)" />
      <path d="M32 11c-7 9.5-14 17.4-14 25.5a14 14 0 0 0 28 0C46 28.4 39 20.5 32 11z" fill="#0B0B0B" />
      <path d="M24.5 40.5l5-5 4 3.5 6.5-7" fill="none" stroke="#4ADE80" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
