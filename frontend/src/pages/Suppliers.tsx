import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, LoaderCircle, TriangleAlert } from 'lucide-react'
import { usePageTitle } from '../hooks/usePageTitle'
import { fetchSuppliers } from '../services/candidateService'
import type { Supplier } from '../types'
import { getErrorMessage } from '../utils/errors'

function money(value: number, currency?: string | null): string {
    try {
        return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: currency && currency !== '?' ? currency : 'EUR' }).format(value)
    } catch {
        return `${value.toLocaleString('fr-FR')} ${currency ?? ''}`
    }
}

export default function Suppliers() {
    usePageTitle('Fournisseurs')
    const [items, setItems] = useState<Supplier[] | null>(null)
    const [error, setError] = useState('')

    useEffect(() => { fetchSuppliers().then(setItems).catch((e) => setError(getErrorMessage(e))) }, [])

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Fournisseurs</h1>
                <p className="muted mt-1">Regroupés automatiquement à partir de tes factures (SIREN, sinon nom normalisé).</p>
            </div>
            {error && <div role="alert" className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">{error}</div>}
            {!items && !error && <div className="grid h-40 place-items-center"><LoaderCircle className="text-brand-500 animate-spin" size={26} /></div>}
            {items?.length === 0 && <div className="card p-10 text-center"><p className="font-bold">Aucun fournisseur</p><p className="muted mt-1 text-sm">Ils apparaissent dès que des factures sont traitées.</p></div>}

            <div className="space-y-3">
                {items?.map((s) => (
                    <details key={s.key} className="card group p-5">
                        <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-3">
                            <div className="min-w-0">
                                <p className="truncate text-lg font-extrabold">{s.name}</p>
                                <p className="muted text-xs">{[s.siret && `SIRET ${s.siret}`, s.vat_number].filter(Boolean).join(' · ') || 'Identifiants non renseignés'}</p>
                            </div>
                            <div className="flex items-center gap-4 text-sm">
                                {s.ibans.length > 1 && (
                                    <span className="inline-flex items-center gap-1 font-semibold text-amber-600 dark:text-amber-400"><TriangleAlert size={15} /> {s.ibans.length} IBAN</span>
                                )}
                                <span className="muted font-semibold">{s.invoice_count} facture{s.invoice_count > 1 ? 's' : ''}</span>
                                <span className="font-bold">{s.totals.map((t) => money(t.total, t.currency)).join(' + ')}</span>
                                <ChevronDown size={18} className="text-brand-500 transition group-open:rotate-180" />
                            </div>
                        </summary>
                        <div className="mt-4 space-y-4 border-t pt-4" style={{ borderColor: 'var(--border)' }}>
                            {s.ibans.length > 0 && (
                                <p className="text-sm"><span className="font-bold">IBAN utilisés : </span>{s.ibans.map((i) => `${i.iban} (${i.count})`).join(' · ')}</p>
                            )}
                            <ul className="divide-y text-sm" style={{ borderColor: 'var(--border)' }}>
                                {s.invoices.map((inv) => (
                                    <li key={inv.document_id} className="flex flex-wrap items-center justify-between gap-2 py-2.5" style={{ borderColor: 'var(--border)' }}>
                                        <Link to={`/app/documents/${inv.document_id}`} className="text-brand-500 font-semibold hover:underline">{inv.number ?? inv.filename}</Link>
                                        <span className="muted">{inv.date ?? '—'}</span>
                                        <span className="font-semibold">{inv.total_ttc != null ? money(inv.total_ttc, inv.currency) : '—'}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </details>
                ))}
            </div>
        </div>
    )
}