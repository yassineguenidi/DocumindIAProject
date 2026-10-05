import type { ReactNode } from 'react'
import { CheckCircle2, Info } from 'lucide-react'

export function Notice({ tone = 'info', children }: { tone?: 'info' | 'success'; children: ReactNode }) {
    const cls = tone === 'success'
        ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
        : 'border-brand-500/30 bg-brand-500/10 text-brand-700 dark:text-brand-200'
    const Icon = tone === 'success' ? CheckCircle2 : Info
    return (
        <div role={tone === 'success' ? 'status' : undefined} className={`flex items-start gap-2.5 rounded-xl border px-4 py-3 text-sm font-semibold ${cls}`}>
            <Icon size={18} className="mt-0.5 shrink-0" />
            <div>{children}</div>
        </div>
    )
}