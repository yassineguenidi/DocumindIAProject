import { useRef, useState } from 'react'
import { AlertCircle, CheckCircle2, LoaderCircle, UploadCloud } from 'lucide-react'
import { useUsage } from '../../contexts/UsageContext'
import { uploadDocument } from '../../services/documentService'
import { getErrorMessage } from '../../utils/errors'
import { useToast } from '../../contexts/ToastContext'

const ACCEPT = ['.pdf', '.png', '.jpg', '.jpeg']

interface Item { id: number; name: string; status: 'uploading' | 'done' | 'error'; progress: number; error?: string }

export function UploadZone({ onUploaded }: { onUploaded?: () => void }) {
    const { usage, refreshUsage } = useUsage()
    const [items, setItems] = useState<Item[]>([])
    const [dragging, setDragging] = useState(false)
    const inputRef = useRef<HTMLInputElement>(null)
    const counter = useRef(0)
    const toast = useToast()

    const patch = (id: number, p: Partial<Item>) =>
        setItems((list) => list.map((i) => (i.id === id ? { ...i, ...p } : i)))

    async function handleFiles(files: FileList | File[]) {
        let added = 0
        for (const file of Array.from(files)) {
            const id = ++counter.current
            setItems((l) => [{ id, name: file.name, status: 'uploading' as const, progress: 0 }, ...l].slice(0, 5))

            const ext = `.${(file.name.split('.').pop() ?? '').toLowerCase()}`
            if (!ACCEPT.includes(ext)) {
                patch(id, { status: 'error', error: 'Format non pris en charge (PDF, PNG, JPG)' })
                continue
            }
            if (usage && file.size > usage.max_file_size_mb * 1024 * 1024) {
                patch(id, { status: 'error', error: `Fichier trop volumineux (max ${usage.max_file_size_mb} Mo)` })
                continue
            }
            try {
                await uploadDocument(file, (progress) => patch(id, { progress }))
                patch(id, { status: 'done', progress: 100 })
                added++
            } catch (err) {
                patch(id, { status: 'error', error: getErrorMessage(err) })
            }
        }
        if (added > 0) toast.success(added > 1 ? `${added} documents ajoutés` : 'Document ajouté')
        await refreshUsage()
        onUploaded?.()
    }

    return (
        <div>
            <div
                role="button"
                tabIndex={0}
                aria-label="Déposer des documents"
                onClick={() => inputRef.current?.click()}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inputRef.current?.click() } }}
                onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => { e.preventDefault(); setDragging(false); void handleFiles(e.dataTransfer.files) }}
                className="cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition"
                style={{
                    borderColor: dragging ? 'var(--color-brand-500)' : 'var(--border)',
                    background: dragging ? 'var(--surface-2)' : 'transparent',
                }}
            >
                <div className="bg-brand-gradient shadow-soft mx-auto grid h-14 w-14 place-items-center rounded-2xl text-white">
                    <UploadCloud size={26} />
                </div>
                <p className="mt-4 font-bold">Glissez vos documents ici</p>
                <p className="muted mt-1 text-sm">ou cliquez pour parcourir</p>
                <p className="muted mt-3 text-xs">PDF, PNG, JPG{usage ? ` · ${usage.max_file_size_mb} Mo max par fichier` : ''}</p>
                <input
                    ref={inputRef}
                    type="file"
                    multiple
                    accept={ACCEPT.join(',')}
                    className="hidden"
                    onChange={(e) => { if (e.target.files) void handleFiles(e.target.files); e.target.value = '' }}
                />
            </div>

            {items.length > 0 && (
                <ul className="mt-4 space-y-2" aria-live="polite">
                    {items.map((i) => (
                        <li key={i.id} className="rounded-xl px-3 py-2.5 text-sm" style={{ background: 'var(--surface-2)' }}>
                            <div className="flex items-center gap-2">
                                {i.status === 'uploading' && <LoaderCircle size={16} className="text-brand-500 shrink-0 animate-spin" />}
                                {i.status === 'done' && <CheckCircle2 size={16} className="shrink-0 text-emerald-500" />}
                                {i.status === 'error' && <AlertCircle size={16} className="shrink-0 text-red-500" />}
                                <span className="truncate font-semibold">{i.name}</span>
                            </div>
                            {i.status === 'uploading' && (
                                <div className="mt-2 h-1.5 overflow-hidden rounded-full" style={{ background: 'var(--border)' }}>
                                    <div className="bg-brand-gradient h-full rounded-full transition-all" style={{ width: `${i.progress}%` }} />
                                </div>
                            )}
                            {i.error && <p className="mt-1 text-xs text-red-500">{i.error}</p>}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}