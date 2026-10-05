import type { DocStatus } from '../../types'

const MAP: Record<DocStatus, { label: string; cls: string }> = {
    uploading: { label: 'Envoi', cls: 'bg-slate-500/15 text-slate-600 dark:text-slate-300' },
    queued: { label: 'En attente', cls: 'bg-amber-500/15 text-amber-700 dark:text-amber-300' },
    ocr: { label: 'Lecture', cls: 'bg-brand-500/15 text-brand-600 dark:text-brand-300' },
    extraction: { label: 'Extraction', cls: 'bg-brand-500/15 text-brand-600 dark:text-brand-300' },
    validation: { label: 'Validation', cls: 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-300' },
    done: { label: 'Terminé', cls: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300' },
    failed: { label: 'Échec', cls: 'bg-red-500/15 text-red-600 dark:text-red-400' },
}

export function StatusBadge({ status }: { status: DocStatus }) {
    const s = MAP[status] ?? MAP.queued
    return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${s.cls}`}>{s.label}</span>
}