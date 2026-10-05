import { motion } from 'motion/react'

const R = 54
const C = 2 * Math.PI * R

export function QuotaRing({ used, quota }: { used: number; quota: number | null }) {
    const unlimited = quota === null
    const pct = unlimited ? 1 : Math.min(used / Math.max(quota, 1), 1)
    const high = !unlimited && pct >= 0.9

    return (
        <div className="relative mx-auto grid w-44 place-items-center">
            <svg viewBox="0 0 128 128" className="h-44 w-44 -rotate-90" aria-hidden="true">
                <defs>
                    <linearGradient id="qr-grad" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0" stopColor="#2147e0" /><stop offset=".55" stopColor="#4f56ee" /><stop offset="1" stopColor="#22b8e8" />
                    </linearGradient>
                </defs>
                <circle cx="64" cy="64" r={R} fill="none" strokeWidth="12" style={{ stroke: 'var(--surface-2)' }} />
                <motion.circle
                    cx="64" cy="64" r={R} fill="none" strokeWidth="12" strokeLinecap="round"
                    stroke={high ? '#ef4444' : 'url(#qr-grad)'}
                    strokeDasharray={C}
                    initial={{ strokeDashoffset: C }}
                    animate={{ strokeDashoffset: C * (1 - pct) }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                />
            </svg>
            <div className="absolute text-center">
                {unlimited ? (
                    <>
                        <p className="text-4xl font-extrabold">∞</p>
                        <p className="muted text-xs font-semibold">Illimité</p>
                    </>
                ) : (
                    <>
                        <p className="text-3xl font-extrabold">{used}<span className="muted text-lg font-semibold"> / {quota}</span></p>
                        <p className="muted text-xs font-semibold">documents ce mois</p>
                    </>
                )}
            </div>
        </div>
    )
}