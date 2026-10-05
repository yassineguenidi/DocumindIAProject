import { Link } from 'react-router-dom'
import { FileImage, FileText, Inbox } from 'lucide-react'
import type { DocumentItem } from '../../types'
import { formatBytes, formatDateTime } from '../../utils/format'
import { StatusBadge } from '../documents/StatusBadge'

export function RecentDocuments({ docs }: { docs: DocumentItem[] }) {
    if (docs.length === 0) {
        return (
            <div className="py-10 text-center">
                <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl" style={{ background: 'var(--surface-2)' }}>
                    <Inbox size={26} className="text-brand-500" />
                </div>
                <p className="mt-4 font-bold">Aucun document pour l'instant</p>
                <p className="muted mt-1 text-sm">Déposez votre premier document pour le voir apparaître ici.</p>
            </div>
        )
    }
    return (
        <ul className="divide-y" style={{ borderColor: 'var(--border)' }}>
            {docs.map((d) => {
                const Icon = d.mime_type.startsWith('image/') ? FileImage : FileText
                return (
                    <li key={d.id} className="flex items-center gap-3 py-3.5" style={{ borderColor: 'var(--border)' }}>
                        <div className="text-brand-500 grid h-10 w-10 shrink-0 place-items-center rounded-xl" style={{ background: 'var(--surface-2)' }}>
                            <Icon size={20} />
                        </div>
                        <div className="min-w-0 flex-1">
                            <p className="truncate font-semibold">{d.original_filename}</p>
                            <p className="muted text-xs">{formatDateTime(d.created_at)} · {formatBytes(d.size_bytes)}</p>
                        </div>
                        <StatusBadge status={d.status} />
                    </li>
                )
            })}
        </ul>
    )
}

export function SeeAll() {
    return <Link to="/app/documents" className="text-brand-500 text-sm font-semibold">Voir tout</Link>
}