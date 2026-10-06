import { useEffect, useRef } from 'react'
import { FileSearch, Download, LoaderCircle, Trash2, X } from 'lucide-react'
import type { DocumentItem } from '../../types'
import { docTypeLabel, formatBytes, formatDateFull } from '../../utils/format'
import { StatusBadge } from './StatusBadge'
import { Link } from 'react-router-dom'

const FIELD_LABELS: Record<string, string> = {
    supplier_name: 'Fournisseur', supplier_address: 'Adresse', supplier_siret: 'SIRET',
    supplier_vat_number: 'N° TVA', customer_name: 'Client', invoice_number: 'N° de facture',
    invoice_date: 'Date', due_date: 'Échéance', currency: 'Devise',
    total_ht: 'Total HT', total_vat: 'TVA', total_ttc: 'Total TTC', language: 'Langue',
    document_kind: 'Type', customer_siren: 'SIREN du client', iban: 'IBAN', lines: 'Lignes', vat_breakdown: 'TVA par taux',
    first_name: 'Prénom', last_name: 'Nom', headline: 'Titre', email: 'E-mail', phone: 'Téléphone',
    location: 'Localisation', links: 'Liens', summary: 'Profil', experiences: 'Expériences',
    education: 'Formations', skills: 'Compétences', languages: 'Langues', certifications: 'Certifications',
    derived: 'Calculé',
}

function ExtractedData({ data }: { data: unknown }) {
    if (!data || typeof data !== 'object') {
        return <p className="muted text-sm">Les données extraites apparaîtront ici une fois le traitement terminé.</p>
    }
    const obj = data as Record<string, unknown>
    const entries = Object.entries(obj).filter(([k]) => !k.startsWith('_'))
    const validation = obj._validation as { ok: boolean; issues: string[] } | undefined

    return (
        <div className="space-y-3">
            {typeof obj._note === 'string' && <p className="muted text-sm">{obj._note}</p>}
            {validation && (
                <div className={`rounded-xl px-3 py-2.5 text-sm font-semibold ${validation.ok ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300' : 'bg-amber-500/15 text-amber-700 dark:text-amber-300'}`}>
                    {validation.ok ? 'Contrôles de cohérence réussis' : 'À vérifier :'}
                    {!validation.ok && <ul className="mt-1 list-disc pl-5 font-normal">{validation.issues.map((i) => <li key={i}>{i}</li>)}</ul>}
                </div>
            )}
            {entries.length > 0 && (
                <dl className="space-y-2">
                    {entries.map(([k, v]) => (
                        <div key={k} className="flex justify-between gap-4 rounded-xl px-3 py-2 text-sm" style={{ background: 'var(--surface-2)' }}>
                            <dt className="muted">{FIELD_LABELS[k] ?? k}</dt>
                            <dd className="text-right font-semibold">
                                {v === null || v === '' ? '—'
                                    : typeof v === 'number' ? v.toLocaleString('fr-FR')
                                        : typeof v === 'object'
                                            ? <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-words text-left text-xs font-normal">{JSON.stringify(v, null, 2)}</pre>
                                            : String(v)}
                            </dd>
                        </div>
                    ))}
                </dl>
            )}
        </div>
    )
}

interface Props {
    doc: DocumentItem
    downloading: boolean
    onClose: () => void
    onDownload: () => void
    onDelete: () => void
}

export function DocumentDrawer({ doc, downloading, onClose, onDownload, onDelete }: Props) {
    const closeRef = useRef<HTMLButtonElement>(null)

    useEffect(() => { closeRef.current?.focus() }, [])
    useEffect(() => {
        const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', onKey)
        return () => window.removeEventListener('keydown', onKey)
    }, [onClose])

    const rows: [string, string][] = [
        ['Type', docTypeLabel(doc.doc_type)],
        ['Taille', formatBytes(doc.size_bytes)],
        ['Format', doc.mime_type],
        ['Ajouté le', formatDateFull(doc.created_at)],
    ]

    return (
        <div className="fixed inset-0 z-50">
            <div className="absolute inset-0 bg-black/40" onClick={onClose} />
            <aside
                role="dialog" aria-modal="true" aria-label="Détail du document"
                className="card absolute inset-y-0 right-0 flex w-full max-w-md flex-col overflow-y-auto rounded-none border-y-0 border-r-0 p-6 shadow-2xl"
            >
                <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                        <h2 className="break-words text-xl font-extrabold">{doc.original_filename}</h2>
                        <div className="mt-2"><StatusBadge status={doc.status} /></div>
                    </div>
                    <button ref={closeRef} onClick={onClose} className="btn-icon shrink-0" aria-label="Fermer"><X size={18} /></button>
                </div>

                {doc.status === 'failed' && doc.error_message && (
                    <p role="alert" className="mt-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">
                        {doc.error_message}
                    </p>
                )}

                <dl className="mt-6 space-y-3 text-sm">
                    {rows.map(([k, v]) => (
                        <div key={k} className="flex justify-between gap-4">
                            <dt className="muted">{k}</dt>
                            <dd className="text-right font-semibold">{v}</dd>
                        </div>
                    ))}
                </dl>

                <h3 className="mb-3 mt-8 font-bold">Données extraites</h3>
                <ExtractedData data={doc.extracted_data} />

                <div className="mt-auto space-y-3 pt-8">
                    {(doc.status === 'done' || doc.status === 'failed') && (
                        <Link to={`/app/documents/${doc.id}`} className="btn-primary w-full">
                            <FileSearch size={16} /> {doc.status === 'done' ? 'Ouvrir la relecture' : 'Voir et relancer'}
                        </Link>
                    )}
                    <div className="grid grid-cols-2 gap-3">
                        <button onClick={onDownload} disabled={downloading} className="btn-ghost">
                            {downloading ? <LoaderCircle size={16} className="animate-spin" /> : <Download size={16} />} Télécharger
                        </button>
                        <button onClick={onDelete} className="btn-ghost text-red-600 dark:text-red-400">
                            <Trash2 size={16} /> Supprimer
                        </button>
                    </div>
                </div>
            </aside>
        </div>
    )
}