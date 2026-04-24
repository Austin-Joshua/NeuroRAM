/** Inline NeuroRAM mark: memory grid + blue/gold accent (no external assets). */
export function NeuroRAMLogo({ size = 36 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      aria-hidden
      className="nr-logo"
    >
      <defs>
        <linearGradient id="nrGold" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#e8c76a" />
          <stop offset="100%" stopColor="#b8891c" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="36" height="36" rx="10" fill="var(--surface-strong, #fff)" stroke="url(#nrGold)" strokeWidth="1.5" />
      <rect x="8" y="10" width="5" height="5" rx="1" fill="#2563eb" opacity="0.9" />
      <rect x="15" y="10" width="5" height="5" rx="1" fill="#2563eb" opacity="0.75" />
      <rect x="22" y="10" width="5" height="5" rx="1" fill="#2563eb" opacity="0.6" />
      <rect x="8" y="17" width="5" height="5" rx="1" fill="#2563eb" opacity="0.75" />
      <rect x="15" y="17" width="5" height="5" rx="1" fill="url(#nrGold)" />
      <rect x="22" y="17" width="5" height="5" rx="1" fill="#2563eb" opacity="0.75" />
      <rect x="8" y="24" width="5" height="5" rx="1" fill="#2563eb" opacity="0.6" />
      <rect x="15" y="24" width="5" height="5" rx="1" fill="#2563eb" opacity="0.85" />
      <rect x="22" y="24" width="5" height="5" rx="1" fill="#2563eb" opacity="0.9" />
      <path d="M28 8 L34 8 L34 14" fill="none" stroke="url(#nrGold)" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}
