import { useState } from 'react'
import {
    ChevronLeft, ChevronRight, Download, FileImage, FileText, Inbox, LoaderCircle,
    Plus, RefreshCw, Search, SearchX, Trash2, FileSearch,
} from 'lucide-react'
import { StatusBadge } from '../components/documents/StatusBadge'
import { DocumentDrawer } from '../components/documents/DocumentDrawer'
import { UploadZone } from '../components/documents/UploadZone'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { useUsage } from '../contexts/UsageContext'
import { PAGE_SIZE, useDocuments } from '../hooks/useDocuments'
import { deleteDocument, downloadDocument } from '../services/documentService'
import type { DocumentItem, StatusFilter } from '../types'
import { getErrorMessage } from '../utils/errors'
import { docTypeLabel, formatBytes, formatDateTime } from '../utils/format'

import { usePageTitle } from '../hooks/usePageTitle'
import { useToast } from '../contexts/ToastContext'

import { Link } from 'react-router-dom'

const TABS: { id: StatusFilter; label: string }[] = [
    { id: 'all', label: 'Tous' },
    { id: 'in_progress', label: 'En cours' },
    { id: 'done', label: 'Terminés' },
    { id: 'failed', label: 'Erreurs' },
]

const iconBtn = 'muted rounded-lg p-2 transition hover:bg-[var(--surface-2)] hover:text-[var(--text)]'

export default function Documents() {
    const { items, total, page, setPage, search, setSearch, status, setStatus, resetFilters, loading, error, reload } = useDocuments()
    const { refreshUsage } = useUsage()

    const [showUpload, setShowUpload] = useState(false)
    const [selected, setSelected] = useState<DocumentItem | null>(null)
    const [toDelete, setToDelete] = useState<DocumentItem | null>(null)
    const [deleting, setDeleting] = useState(false)
    const [deleteError, setDeleteError] = useState('')
    const [actionError, setActionError] = useState('')
    const [downloadingId, setDownloadingId] = useState<number | null>(null)

    const filtered = search.trim() !== '' || status !== 'all'
    const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))
    const from = total === 0 ? 0 : page * PAGE_SIZE + 1
    const to = Math.min((page + 1) * PAGE_SIZE, total)

    const selectedDoc = selected ? (items.find((d) => d.id === selected.id) ?? selected) : null

    const toast = useToast()
    async function handleDownload(doc: DocumentItem) {
        setDownloadingId(doc.id)
        setActionError('')
        try {
            await downloadDocument(doc.id, doc.original_filename)
        } catch (e) {
            setActionError(getErrorMessage(e))
        } finally {
            setDownloadingId(null)
        }
    }

    async function confirmDelete() {
        if (!toDelete) return
        setDeleting(true)
        setDeleteError('')
        try {
            await deleteDocument(toDelete.id)
            if (selected?.id === toDelete.id) setSelected(null)
            setToDelete(null)
            toast.success('Document supprimé')

            await Promise.all([reload(), refreshUsage()])
        } catch (e) {
            setDeleteError(getErrorMessage(e))
        } finally {
            setDeleting(false)
        }
    }
    usePageTitle('Documents')
    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Documents</h1>
                    <p className="muted mt-1">Retrouvez, téléchargez et gérez tous vos documents.</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={() => void reload()} className="btn-icon" aria-label="Actualiser la liste">
                        <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                    </button>
                    <button onClick={() => setShowUpload(!showUpload)} className="btn-primary" aria-expanded={showUpload}>
                        <Plus size={18} /> Ajouter des documents
                    </button>
                </div>
            </div>

            {showUpload && (
                <div className="card p-6">
                    <UploadZone onUploaded={() => { setPage(0); void reload() }} />
                </div>
            )}

            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="relative w-full sm:max-w-sm">
                    <Search size={18} className="muted absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                        type="search" value={search} onChange={(e) => setSearch(e.target.value)}
                        placeholder="Rechercher un document…" aria-label="Rechercher un document"
                        className="input pl-11" maxLength={100}
                    />
                </div>
                <div role="group" aria-label="Filtrer par statut" className="flex gap-1 rounded-xl p-1" style={{ background: 'var(--surface-2)' }}>
                    {TABS.map((t) => (
                        <button
                            key={t.id} onClick={() => setStatus(t.id)} aria-pressed={status === t.id}
                            className={`rounded-lg px-3.5 py-2 text-sm font-semibold transition ${status === t.id ? 'bg-[var(--surface)] shadow-sm' : 'muted hover:text-[var(--text)]'}`}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>
            </div>

            {(error || actionError) && (
                <div role="alert" className="flex items-center justify-between gap-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">
                    {error || actionError}
                    {error && <button onClick={() => void reload()} className="font-bold underline">Réessayer</button>}
                </div>
            )}

            <div className="card overflow-hidden">
                {!loading && items.length === 0 ? (
                    <div className="px-6 py-16 text-center">
                        <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl" style={{ background: 'var(--surface-2)' }}>
                            {filtered ? <SearchX size={26} className="text-brand-500" /> : <Inbox size={26} className="text-brand-500" />}
                        </div>
                        <p className="mt-4 font-bold">{filtered ? 'Aucun résultat' : 'Aucun document pour le moment'}</p>
                        <p className="muted mt-1 text-sm">
                            {filtered ? 'Essayez une autre recherche ou un autre filtre.' : 'Ajoutez votre premier document pour commencer.'}
                        </p>
                        <button onClick={filtered ? resetFilters : () => setShowUpload(true)} className="btn-ghost mt-5">
                            {filtered ? 'Réinitialiser les filtres' : 'Ajouter des documents'}
                        </button>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="muted text-xs uppercase tracking-wider">
                                <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                                    <th className="px-5 py-3 font-semibold">Document</th>
                                    <th className="hidden px-3 py-3 font-semibold md:table-cell">Type</th>
                                    <th className="px-3 py-3 font-semibold">Statut</th>
                                    <th className="hidden px-3 py-3 font-semibold lg:table-cell">Taille</th>
                                    <th className="hidden px-3 py-3 font-semibold sm:table-cell">Date</th>
                                    <th className="px-5 py-3"><span className="sr-only">Actions</span></th>
                                </tr>
                            </thead>
                            <tbody className={loading && items.length > 0 ? 'opacity-60 transition' : 'transition'}>
                                {loading && items.length === 0 &&
                                    Array.from({ length: 5 }).map((_, i) => (
                                        <tr key={i} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                                            <td colSpan={6} className="px-5 py-4">
                                                <div className="h-10 animate-pulse rounded-xl" style={{ background: 'var(--surface-2)' }} />
                                            </td>
                                        </tr>
                                    ))}
                                {items.map((d) => {
                                    const Icon = d.mime_type.startsWith('image/') ? FileImage : FileText
                                    return (
                                        <tr key={d.id} className="border-b transition last:border-0 hover:bg-[var(--surface-2)]" style={{ borderColor: 'var(--border)' }}>
                                            <td className="px-5 py-3.5">
                                                <button onClick={() => setSelected(d)} className="flex items-center gap-3 text-left" aria-label={`Voir le détail de ${d.original_filename}`}>
                                                    <span className="text-brand-500 grid h-10 w-10 shrink-0 place-items-center rounded-xl" style={{ background: 'var(--surface-2)' }}>
                                                        <Icon size={20} />
                                                    </span>
                                                    <span className="max-w-[10rem] truncate font-semibold sm:max-w-[16rem]">{d.original_filename}</span>
                                                </button>
                                            </td>
                                            <td className="hidden px-3 py-3.5 md:table-cell">{docTypeLabel(d.doc_type)}</td>
                                            <td className="px-3 py-3.5"><StatusBadge status={d.status} /></td>
                                            <td className="muted hidden px-3 py-3.5 lg:table-cell">{formatBytes(d.size_bytes)}</td>
                                            <td className="muted hidden px-3 py-3.5 sm:table-cell">{formatDateTime(d.created_at)}</td>
                                            <td className="px-5 py-3.5">
                                                <div className="flex justify-end gap-1">

                                                    <Link to={`/app/documents/${d.id}`} className={iconBtn} aria-label={`Relire ${d.original_filename}`}>
                                                        <FileSearch size={18} />
                                                    </Link>
                                                    <button onClick={() => void handleDownload(d)} disabled={downloadingId === d.id} className={iconBtn} aria-label={`Télécharger ${d.original_filename}`}>
                                                        {downloadingId === d.id ? <LoaderCircle size={18} className="animate-spin" /> : <Download size={18} />}
                                                    </button>
                                                    <button onClick={() => { setDeleteError(''); setToDelete(d) }} className={`${iconBtn} hover:!text-red-500`} aria-label={`Supprimer ${d.original_filename}`}>
                                                        <Trash2 size={18} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                )}

                {total > 0 && (
                    <div className="flex items-center justify-between border-t px-5 py-3 text-sm" style={{ borderColor: 'var(--border)' }}>
                        <p className="muted">{from}–{to} sur {total}</p>
                        <div className="flex items-center gap-2">
                            <button className="btn-icon" disabled={page === 0} onClick={() => setPage(page - 1)} aria-label="Page précédente"><ChevronLeft size={18} /></button>
                            <span className="muted px-1 font-semibold">{page + 1} / {pageCount}</span>
                            <button className="btn-icon" disabled={page + 1 >= pageCount} onClick={() => setPage(page + 1)} aria-label="Page suivante"><ChevronRight size={18} /></button>
                        </div>
                    </div>
                )}
            </div>

            {selectedDoc && (
                <DocumentDrawer
                    doc={selectedDoc}
                    downloading={downloadingId === selectedDoc.id}
                    onClose={() => setSelected(null)}
                    onDownload={() => void handleDownload(selectedDoc)}
                    onDelete={() => { setDeleteError(''); setToDelete(selectedDoc) }}
                />
            )}

            {toDelete && (
                <ConfirmDialog
                    title="Supprimer ce document ?"
                    message={`« ${toDelete.original_filename} » et son fichier seront définitivement supprimés. Cette action est irréversible.`}
                    confirmLabel="Supprimer"
                    loading={deleting}
                    error={deleteError}
                    onConfirm={() => void confirmDelete()}
                    onCancel={() => setToDelete(null)}
                />
            )}
        </div>
    )
}