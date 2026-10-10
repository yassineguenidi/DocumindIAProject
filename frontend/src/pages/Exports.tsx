import { useState, type ReactNode } from 'react'
import { FileJson, FileSpreadsheet, LoaderCircle } from 'lucide-react'
import { Notice } from '../components/ui/Notice'
import { useToast } from '../contexts/ToastContext'
import { usePageTitle } from '../hooks/usePageTitle'
import { downloadExport } from '../services/exportService'
import { getErrorMessage } from '../utils/errors'

function Section({ title, text, children }: { title: string; text: string; children: ReactNode }) {
    return (
        <section className="card space-y-5 p-6">
            <div>
                <h2 className="text-lg font-bold">{title}</h2>
                <p className="muted text-sm">{text}</p>
            </div>
            {children}
        </section>
    )
}

export default function Exports() {
    usePageTitle('Exports')
    const toast = useToast()
    const [from, setFrom] = useState('')
    const [to, setTo] = useState('')
    const [validatedOnly, setValidatedOnly] = useState(false)
    const [anonymous, setAnonymous] = useState(false)
    const [busy, setBusy] = useState<string | null>(null)

    async function run(key: string, path: string, params: Record<string, unknown>, filename: string) {
        setBusy(key)
        try { await downloadExport(path, params, filename) } catch (e) { toast.error(getErrorMessage(e)) } finally { setBusy(null) }
    }

    const today = new Date().toISOString().slice(0, 10)
    const invoiceParams = { date_from: from || undefined, date_to: to || undefined, validated_only: validatedOnly }
    const btn = (key: string, label: string, icon: ReactNode, onClick: () => void) => (
        <button onClick={onClick} disabled={busy !== null} className="btn-ghost disabled:opacity-60">
            {busy === key ? <LoaderCircle size={16} className="animate-spin" /> : icon} {label}
        </button>
    )

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Exports</h1>
                <p className="muted mt-1">Récupère tes données dans un format réutilisable.</p>
            </div>

            <Section title="Factures" text="Une ligne par facture, plus les lignes de détail et la TVA par taux, prêtes pour la comptabilité.">
                <div className="grid gap-4 sm:grid-cols-3">
                    <div>
                        <label htmlFor="from" className="mb-1.5 block text-sm font-semibold">Du</label>
                        <input id="from" type="date" className="input" value={from} onChange={(e) => setFrom(e.target.value)} />
                    </div>
                    <div>
                        <label htmlFor="to" className="mb-1.5 block text-sm font-semibold">Au</label>
                        <input id="to" type="date" className="input" value={to} onChange={(e) => setTo(e.target.value)} />
                    </div>
                    <label className="flex items-center gap-2 self-end pb-3 text-sm font-semibold">
                        <input type="checkbox" className="h-5 w-5 accent-[var(--color-brand-500)]" checked={validatedOnly} onChange={(e) => setValidatedOnly(e.target.checked)} />
                        Factures validées uniquement
                    </label>
                </div>
                <div className="flex flex-wrap gap-3">
                    {btn('inv-x', 'Excel (.xlsx)', <FileSpreadsheet size={16} />, () => void run('inv-x', '/exports/invoices.xlsx', invoiceParams, `factures-${today}.xlsx`))}
                    {btn('inv-j', 'JSON', <FileJson size={16} />, () => void run('inv-j', '/exports/invoices.json', invoiceParams, `factures-${today}.json`))}
                </div>
            </Section>

            <Section title="Candidats" text="Le vivier de CV traités : identité, expérience, compétences et langues.">
                <label className="flex items-center gap-2 text-sm font-semibold">
                    <input type="checkbox" className="h-5 w-5 accent-[var(--color-brand-500)]" checked={anonymous} onChange={(e) => setAnonymous(e.target.checked)} />
                    Anonymiser (sans nom, e-mail ni téléphone)
                </label>
                {!anonymous && <Notice>Cet export contient des données personnelles : limite son partage et sa durée de conservation (RGPD).</Notice>}
                <div className="flex flex-wrap gap-3">
                    {btn('cand-x', 'Excel (.xlsx)', <FileSpreadsheet size={16} />, () => void run('cand-x', '/exports/candidates.xlsx', { anonymous }, `candidats-${today}.xlsx`))}
                    {btn('cand-j', 'JSON', <FileJson size={16} />, () => void run('cand-j', '/exports/candidates.json', { anonymous }, `candidats-${today}.json`))}
                </div>
            </Section>
        </div>
    )
}