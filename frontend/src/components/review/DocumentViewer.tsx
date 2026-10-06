import { useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight, LoaderCircle } from 'lucide-react'
import { fetchPageImage } from '../../services/documentService'
import type { Layout } from '../../types'
import type { Box } from '../../utils/locate'

export function DocumentViewer({ docId, layout, boxes, page, onPage }: {
    docId: number; layout: Layout; boxes: Box[]; page: number; onPage: (n: number) => void
}) {
    const [urls, setUrls] = useState<Record<number, string>>({})
    const [failed, setFailed] = useState<Record<number, boolean>>({})
    const requested = useRef(new Set<number>())
    const created = useRef<string[]>([])

    const pages = layout.pages
    const current = pages.find((p) => p.number === page) ?? pages[0]
    const number = current?.number ?? 1
    const pageBoxes = boxes.filter((b) => b.page === number)

    useEffect(() => {
        if (!current || requested.current.has(number)) return
        requested.current.add(number)
        fetchPageImage(docId, number)
            .then((url) => { created.current.push(url); setUrls((u) => ({ ...u, [number]: url })) })
            .catch(() => setFailed((f) => ({ ...f, [number]: true })))
    }, [docId, number, current])

    useEffect(() => () => { created.current.forEach((u) => URL.revokeObjectURL(u)) }, [])

    useEffect(() => {
        if (pageBoxes.length === 0) return
        const t = setTimeout(() => document.getElementById('hl-0')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }), 60)
        return () => clearTimeout(t)
    }, [boxes, number, pageBoxes.length])

    if (!current) return <p className="muted text-sm">Aucune page à afficher.</p>

    return (
        <div>
            <div className="mb-3 flex items-center justify-between">
                <p className="muted text-sm font-semibold">Page {number} / {pages.length}</p>
                <div className="flex gap-2">
                    <button className="btn-icon" disabled={number <= 1} onClick={() => onPage(number - 1)} aria-label="Page précédente"><ChevronLeft size={18} /></button>
                    <button className="btn-icon" disabled={number >= pages.length} onClick={() => onPage(number + 1)} aria-label="Page suivante"><ChevronRight size={18} /></button>
                </div>
            </div>

            <div
                className="relative w-full overflow-hidden rounded-xl border shadow-sm"
                style={{ aspectRatio: `${current.width} / ${current.height}`, borderColor: 'var(--border)', background: 'var(--surface-2)' }}
            >
                {urls[number] ? (
                    <img src={urls[number]} alt={`Page ${number} du document`} className="absolute inset-0 h-full w-full select-none object-contain" draggable={false} />
                ) : failed[number] ? (
                    <p className="muted absolute inset-0 grid place-items-center p-6 text-center text-sm">Impossible d'afficher cette page.</p>
                ) : (
                    <div className="absolute inset-0 grid place-items-center"><LoaderCircle className="text-brand-500 animate-spin" size={26} /></div>
                )}
                {pageBoxes.map((b, i) => (
                    <div
                        id={`hl-${i}`} key={i} aria-hidden="true"
                        className="pointer-events-none absolute rounded-sm bg-amber-300/40 ring-2 ring-amber-500"
                        style={{ left: `${b.x * 100}%`, top: `${b.y * 100}%`, width: `${b.w * 100}%`, height: `${b.h * 100}%` }}
                    />
                ))}
            </div>
        </div>
    )
}