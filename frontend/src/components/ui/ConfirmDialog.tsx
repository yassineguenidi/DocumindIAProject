import { useEffect, useRef } from 'react'
import { ArrowRightLeft, LoaderCircle, TriangleAlert } from 'lucide-react'

interface Props {
    title: string
    message: string
    confirmLabel: string
    tone?: 'danger' | 'primary'
    loading?: boolean
    error?: string
    onConfirm: () => void
    onCancel: () => void
}

export function ConfirmDialog({ title, message, confirmLabel, tone = 'danger', loading, error, onConfirm, onCancel }: Props) {
    const cancelRef = useRef<HTMLButtonElement>(null)
    const danger = tone === 'danger'

    useEffect(() => { cancelRef.current?.focus() }, [])

    useEffect(() => {
        const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && !loading) onCancel() }
        window.addEventListener('keydown', onKey)
        return () => window.removeEventListener('keydown', onKey)
    }, [loading, onCancel])

    return (
        <div className="fixed inset-0 z-[60] grid place-items-center p-5">
            <div className="absolute inset-0 bg-black/50" onClick={() => { if (!loading) onCancel() }} />
            <div
                role="alertdialog" aria-modal="true" aria-labelledby="cd-title" aria-describedby="cd-msg"
                className="card shadow-soft relative w-full max-w-md p-6"
            >
                <div className="flex gap-4">
                    <div className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ${danger ? 'bg-red-500/15 text-red-500' : 'bg-brand-500/15 text-brand-500'}`}>
                        {danger ? <TriangleAlert size={22} /> : <ArrowRightLeft size={22} />}
                    </div>
                    <div>
                        <h2 id="cd-title" className="text-lg font-bold">{title}</h2>
                        <p id="cd-msg" className="muted mt-1 text-sm">{message}</p>
                        {error && <p role="alert" className="mt-3 text-sm text-red-500">{error}</p>}
                    </div>
                </div>
                <div className="mt-6 flex justify-end gap-3">
                    <button ref={cancelRef} onClick={onCancel} disabled={loading} className="btn-ghost">Annuler</button>
                    <button
                        onClick={onConfirm} disabled={loading}
                        className={`inline-flex items-center gap-2 rounded-xl px-5 py-3 font-semibold text-white transition disabled:opacity-60 ${danger ? 'bg-red-600 hover:bg-red-700' : 'bg-brand-gradient shadow-soft'}`}
                    >
                        {loading && <LoaderCircle size={16} className="animate-spin" />} {confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    )
}











// import { useEffect, useRef } from 'react'
// import { LoaderCircle, TriangleAlert } from 'lucide-react'

// interface Props {
//     title: string
//     message: string
//     confirmLabel: string
//     loading?: boolean
//     error?: string
//     onConfirm: () => void
//     onCancel: () => void
// }

// export function ConfirmDialog({ title, message, confirmLabel, loading, error, onConfirm, onCancel }: Props) {
//     const cancelRef = useRef<HTMLButtonElement>(null)

//     useEffect(() => { cancelRef.current?.focus() }, [])

//     useEffect(() => {
//         const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && !loading) onCancel() }
//         window.addEventListener('keydown', onKey)
//         return () => window.removeEventListener('keydown', onKey)
//     }, [loading, onCancel])

//     return (
//         <div className="fixed inset-0 z-[60] grid place-items-center p-5">
//             <div className="absolute inset-0 bg-black/50" onClick={() => { if (!loading) onCancel() }} />
//             <div
//                 role="alertdialog" aria-modal="true" aria-labelledby="cd-title" aria-describedby="cd-msg"
//                 className="card shadow-soft relative w-full max-w-md p-6"
//             >
//                 <div className="flex gap-4">
//                     <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-red-500/15 text-red-500">
//                         <TriangleAlert size={22} />
//                     </div>
//                     <div>
//                         <h2 id="cd-title" className="text-lg font-bold">{title}</h2>
//                         <p id="cd-msg" className="muted mt-1 text-sm">{message}</p>
//                         {error && <p role="alert" className="mt-3 text-sm text-red-500">{error}</p>}
//                     </div>
//                 </div>
//                 <div className="mt-6 flex justify-end gap-3">
//                     <button ref={cancelRef} onClick={onCancel} disabled={loading} className="btn-ghost">Annuler</button>
//                     <button
//                         onClick={onConfirm} disabled={loading}
//                         className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-5 py-3 font-semibold text-white transition hover:bg-red-700 disabled:opacity-60"
//                     >
//                         {loading && <LoaderCircle size={16} className="animate-spin" />} {confirmLabel}
//                     </button>
//                 </div>
//             </div>
//         </div>
//     )
// }