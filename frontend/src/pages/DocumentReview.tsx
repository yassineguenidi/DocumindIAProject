import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, BadgeCheck, Download, LoaderCircle, RefreshCw, Save, TriangleAlert } from 'lucide-react'
import { StatusBadge } from '../components/documents/StatusBadge'
import { DocumentViewer } from '../components/review/DocumentViewer'
import { ReviewForm, type Draft } from '../components/review/ReviewForm'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { Notice } from '../components/ui/Notice'
import { useToast } from '../contexts/ToastContext'
import { pruneDraft, SPECS } from '../data/reviewSpecs'
import { usePageTitle } from '../hooks/usePageTitle'
import { downloadDocument, fetchDocument, fetchLayout, reprocessDocument, saveReview } from '../services/documentService'
import type { DocumentItem, Layout, Review, ValidationIssue } from '../types'
import { getErrorMessage } from '../utils/errors'
import { formatDateFull } from '../utils/format'
import { locate } from '../utils/locate'

const ACTIVE = ['uploading', 'queued', 'ocr', 'extraction', 'validation']

function toDraft(data: unknown): Draft | null {
    if (!data || typeof data !== 'object') return null
    return Object.fromEntries(Object.entries(data as Record<string, unknown>).filter(([k]) => !k.startsWith('_') && k !== 'derived'))
}

function Message({ title, children }: { title: string; children: ReactNode }) {
    return (
        <div className="card mx-auto max-w-lg space-y-4 p-10 text-center">
            <h2 className="text-xl font-extrabold">{title}</h2>
            {children}
        </div>
    )
}

export default function DocumentReview() {
    usePageTitle('Relecture')
    const docId = Number(useParams().id)
    const toast = useToast()

    const [doc, setDoc] = useState<DocumentItem | null>(null)
    const [layout, setLayout] = useState<Layout | null>(null)
    const [layoutFailed, setLayoutFailed] = useState(false)
    const [error, setError] = useState('')
    const [draft, setDraft] = useState<Draft | null>(null)
    const [active, setActive] = useState<{ id: string; value: unknown } | null>(null)
    const [page, setPage] = useState(1)
    const [busy, setBusy] = useState<'save' | 'validate' | 'reprocess' | null>(null)
    const [confirmRerun, setConfirmRerun] = useState(false)
    const [downloading, setDownloading] = useState(false)

    useEffect(() => {
        if (!Number.isFinite(docId)) { setError('Document introuvable'); return }
        let cancelled = false
        fetchDocument(docId).then((d) => { if (!cancelled) setDoc(d) }).catch((e) => { if (!cancelled) setError(getErrorMessage(e)) })
        fetchLayout(docId).then((l) => { if (!cancelled) setLayout(l) }).catch(() => { if (!cancelled) setLayoutFailed(true) })
        return () => { cancelled = true }
    }, [docId])

    // Tant que le document est en cours de traitement (après « Relancer »), on rafraîchit
    const processing = doc ? ACTIVE.includes(doc.status) : false
    useEffect(() => {
        if (!processing) return
        const t = setInterval(() => { fetchDocument(docId).then(setDoc).catch(() => { /* on réessaie */ }) }, 3000)
        return () => clearInterval(t)
    }, [processing, docId])

    const original = useMemo(() => (doc?.status === 'done' ? toDraft(doc.extracted_data) : null), [doc])
    useEffect(() => { setDraft(original) }, [original])

    const dirty = useMemo(
        () => draft !== null && original !== null && JSON.stringify(draft) !== JSON.stringify(original),
        [draft, original],
    )
    useEffect(() => {
        if (!dirty) return
        const warn = (e: BeforeUnloadEvent) => { e.preventDefault() }
        window.addEventListener('beforeunload', warn)
        return () => window.removeEventListener('beforeunload', warn)
    }, [dirty])

    const { details, review } = useMemo(() => {
        const d = (doc?.extracted_data ?? {}) as {
            _validation?: { details?: ValidationIssue[]; issues?: string[] }
            _review?: Review
        }
        const list: ValidationIssue[] = d._validation?.details
            ?? (d._validation?.issues ?? []).map((message) => ({ code: '', severity: 'warning' as const, message, field: null }))
        return { details: list, review: d._review }
    }, [doc])

    const issuesByField = useMemo(() => {
        const map: Record<string, string[]> = {}
        for (const i of details) if (i.field) (map[i.field] ??= []).push(i.message)
        return map
    }, [details])

    const boxes = useMemo(() => (layout && active ? locate(layout.pages, active.value) : []), [layout, active])
    useEffect(() => {
        if (boxes.length > 0) setPage((p) => (boxes.some((b) => b.page === p) ? p : boxes[0].page))
    }, [boxes])

    const spec = doc?.doc_type ? SPECS[doc.doc_type] : undefined
    const hasWords = !!layout && layout.pages.some((p) => p.words.length > 0)

    async function save(markValidated: boolean) {
        if (!doc || !draft || !spec) return
        setBusy(markValidated ? 'validate' : 'save')
        try {
            setDoc(await saveReview(doc.id, pruneDraft(spec, draft), markValidated))
            toast.success(markValidated ? 'Document validé' : 'Corrections enregistrées')
        } catch (e) {
            toast.error(getErrorMessage(e))
        } finally {
            setBusy(null)
        }
    }

    async function rerun() {
        setBusy('reprocess')
        try {
            setDoc(await reprocessDocument(docId))
            setDraft(null)
            setActive(null)
        } catch (e) {
            toast.error(getErrorMessage(e))
        } finally {
            setConfirmRerun(false)
            setBusy(null)
        }
    }

    async function download() {
        if (!doc) return
        setDownloading(true)
        try { await downloadDocument(doc.id, doc.original_filename) } catch (e) { toast.error(getErrorMessage(e)) } finally { setDownloading(false) }
    }

    const back = (
        <Link to="/app/documents" className="muted mb-2 inline-flex items-center gap-1.5 text-sm font-semibold hover:text-[var(--text)]">
            <ArrowLeft size={16} /> Documents
        </Link>
    )

    if (error) return <Message title="Document introuvable"><p className="muted">{error}</p><Link to="/app/documents" className="btn-ghost">Retour aux documents</Link></Message>
    if (!doc) return <div className="grid place-items-center py-24"><LoaderCircle className="text-brand-500 animate-spin" size={28} /></div>

    if (processing) {
        return (
            <Message title="Traitement en cours">
                <LoaderCircle className="text-brand-500 mx-auto animate-spin" size={28} />
                <p className="muted">« {doc.original_filename} » est en cours d'analyse. Cette page se met à jour toute seule.</p>
                <StatusBadge status={doc.status} />
            </Message>
        )
    }

    if (doc.status === 'failed') {
        return (
            <Message title="Le traitement a échoué">
                <p className="muted">{doc.error_message ?? 'Une erreur est survenue.'}</p>
                <div className="flex justify-center gap-3">
                    <Link to="/app/documents" className="btn-ghost">Retour</Link>
                    <button onClick={() => void rerun()} disabled={busy !== null} className="btn-primary">
                        {busy === 'reprocess' ? <LoaderCircle size={16} className="animate-spin" /> : <RefreshCw size={16} />} Relancer
                    </button>
                </div>
            </Message>
        )
    }

    if (!spec || !draft) {
        return (
            <Message title="Relecture indisponible">
                <p className="muted">Ce type de document ({doc.doc_type ?? 'inconnu'}) ne peut pas encore être relu.</p>
                <Link to="/app/documents" className="btn-ghost">Retour aux documents</Link>
            </Message>
        )
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0">
                    {back}
                    <h1 className="break-words text-2xl font-extrabold tracking-tight sm:text-3xl">{doc.original_filename}</h1>
                    <div className="mt-2 flex flex-wrap items-center gap-3">
                        <StatusBadge status={doc.status} />
                        {review?.validated && (
                            <span className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                                <BadgeCheck size={16} /> Validé le {formatDateFull(review.at)}
                            </span>
                        )}
                        {dirty && <span className="text-sm font-semibold text-amber-600 dark:text-amber-400">Modifications non enregistrées</span>}
                    </div>
                </div>
                <div className="flex flex-wrap gap-2">
                    <button onClick={() => void download()} disabled={downloading} className="btn-icon" aria-label="Télécharger l'original">
                        {downloading ? <LoaderCircle size={18} className="animate-spin" /> : <Download size={18} />}
                    </button>
                    <button onClick={() => setConfirmRerun(true)} disabled={busy !== null} className="btn-ghost"><RefreshCw size={16} /> Relancer</button>
                    <button onClick={() => void save(false)} disabled={!dirty || busy !== null} className="btn-ghost disabled:opacity-60">
                        {busy === 'save' ? <LoaderCircle size={16} className="animate-spin" /> : <Save size={16} />} Enregistrer
                    </button>
                    <button onClick={() => void save(true)} disabled={busy !== null || (!!review?.validated && !dirty)} className="btn-primary disabled:opacity-60">
                        {busy === 'validate' ? <LoaderCircle size={16} className="animate-spin" /> : <BadgeCheck size={16} />} Valider
                    </button>
                </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)]">
                <div className="lg:sticky lg:top-20 lg:max-h-[calc(100vh-6rem)] lg:self-start lg:overflow-y-auto">
                    {layout ? (
                        <DocumentViewer docId={doc.id} layout={layout} boxes={boxes} page={page} onPage={setPage} />
                    ) : layoutFailed ? (
                        <Notice>L'aperçu du document est indisponible, mais tu peux relire et corriger les champs.</Notice>
                    ) : (
                        <div className="grid h-64 place-items-center"><LoaderCircle className="text-brand-500 animate-spin" size={26} /></div>
                    )}
                    {layout && !hasWords && (
                        <p className="muted mt-3 text-xs">Document numérisé : le surlignage des champs n'est pas disponible pour ce type de fichier.</p>
                    )}
                    {layout && hasWords && <p className="muted mt-3 text-xs">Clique dans un champ pour voir où il se trouve dans le document.</p>}
                </div>

                <div className="space-y-6">
                    {review?.validated_with_issues && <Notice>Ce document a été validé avec des points encore signalés.</Notice>}
                    {details.length > 0 && (
                        <div className="card space-y-2 p-4">
                            <p className="flex items-center gap-2 font-bold"><TriangleAlert size={18} className="text-amber-500" /> À vérifier ({details.length})</p>
                            <ul className="space-y-1.5 text-sm">
                                {details.map((i, k) => (
                                    <li key={k}>
                                        {i.field ? (
                                            <button type="button" className="text-left underline-offset-2 hover:underline" onClick={() => document.getElementById(`f-${i.field}`)?.focus()}>
                                                {i.message}
                                            </button>
                                        ) : i.message}
                                        {i.ref_document_id && (
                                            <> <Link to={`/app/documents/${i.ref_document_id}`} className="text-brand-500 font-semibold underline">Voir le document</Link></>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                    <div className="card p-5 sm:p-6">
                        <ReviewForm spec={spec} draft={draft} onChange={setDraft} onActive={(id, value) => setActive({ id, value })} issues={issuesByField} />
                    </div>
                </div>
            </div>

            {confirmRerun && (
                <ConfirmDialog
                    title="Relancer l'extraction ?"
                    message="Le document sera analysé de nouveau. Les corrections et la validation actuelles seront perdues."
                    confirmLabel="Relancer"
                    loading={busy === 'reprocess'}
                    onConfirm={() => void rerun()}
                    onCancel={() => setConfirmRerun(false)}
                />
            )}
        </div>
    )
}