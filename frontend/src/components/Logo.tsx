export function Logo({ withText = true, size = 36 }: { withText?: boolean; size?: number }) {
    return (
        <span className="inline-flex items-center gap-2.5">
            <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden="true">
                <defs>
                    <linearGradient id="dm-logo" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                        <stop stopColor="#2147E0" /><stop offset=".55" stopColor="#4F56EE" /><stop offset="1" stopColor="#22B8E8" />
                    </linearGradient>
                </defs>
                <rect width="40" height="40" rx="12" fill="url(#dm-logo)" />
                <path d="M13 8h10l7 7v17a2 2 0 0 1-2 2H13a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2Z" fill="#fff" />
                <path d="M23 8v5a2 2 0 0 0 2 2h5z" fill="#BCD2FF" />
                <rect x="15" y="19" width="10" height="2" rx="1" fill="#4F56EE" />
                <rect x="15" y="23.5" width="7" height="2" rx="1" fill="#4F56EE" fillOpacity=".6" />
                <path d="M29.5 24.5l1.3 3.2 3.2 1.3-3.2 1.3-1.3 3.2-1.3-3.2-3.2-1.3 3.2-1.3z" fill="#22D3EE" stroke="#fff" strokeWidth="1.5" strokeLinejoin="round" />
            </svg>
            {withText && (
                <span className="text-xl font-extrabold tracking-tight">
                    Docu<span className="text-gradient">Mind</span>
                </span>
            )}
        </span>
    )
}