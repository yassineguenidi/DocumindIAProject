import type { LayoutPage } from '../types'

export interface Box { page: number; x: number; y: number; w: number; h: number }

const MAX_BOXES = 8
const ISO = /^(\d{4})-(\d{2})-(\d{2})$/

const fold = (s: string) => s.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
const norm = (s: string) => fold(s).replace(/[^\p{L}\p{N}]/gu, '')
const digits = (s: string) => s.replace(/\D/g, '')

// 2025-07-30 → 30/07/2025, 07/30/2025, 30/07/25... (séparateurs - . / ramenés à /)
function dateForms(iso: string): Set<string> {
    const out = new Set<string>()
    const m = ISO.exec(iso)
    if (!m) return out
    const [, y, mo, d] = m
    const yy = y.slice(2)
    for (const [a, b] of [[d, mo], [mo, d], [String(+d), String(+mo)], [String(+mo), String(+d)]]) {
        out.add(`${a}/${b}/${y}`)
        out.add(`${a}/${b}/${yy}`)
    }
    out.add(`${y}/${mo}/${d}`)
    return out
}

const boxOf = (page: LayoutPage, i: number): Box => {
    const w = page.words[i]
    return { page: page.number, x: w.x, y: w.y, w: w.w, h: w.h }
}

export function locate(pages: LayoutPage[], value: unknown): Box[] {
    if (value === null || value === undefined || value === '' || typeof value === 'boolean') return []
    const found: Box[] = []

    if (typeof value === 'number') {
        const cents = String(Math.round(Math.abs(value) * 100))
        const whole = Number.isInteger(value) ? String(Math.abs(value)) : null
        for (const p of pages) {
            p.words.forEach((w, i) => {
                const d = digits(w.t)
                if (d && (d === cents || d === whole)) found.push(boxOf(p, i))
            })
        }
        return found.slice(0, MAX_BOXES)
    }

    const text = String(value).trim()
    const forms = dateForms(text)
    if (forms.size > 0) {
        for (const p of pages) {
            p.words.forEach((w, i) => {
                if (forms.has(w.t.replace(/[,;:]+$/, '').replace(/[-.]/g, '/'))) found.push(boxOf(p, i))
            })
        }
        return found.slice(0, MAX_BOXES)
    }

    const tokens = text.split(/\s+/).map(norm).filter(Boolean).slice(0, 6)
    if (tokens.length === 0) return []
    for (const p of pages) {
        const words = p.words.map((w) => norm(w.t))
        for (let i = 0; i + tokens.length <= words.length; i++) {
            const hit = tokens.length === 1
                ? words[i] === tokens[0] || (tokens[0].length >= 4 && words[i].includes(tokens[0]))
                : tokens.every((t, k) => words[i + k] === t)
            if (hit) {
                for (let k = 0; k < tokens.length; k++) found.push(boxOf(p, i + k))
                i += tokens.length - 1
            }
        }
    }
    return found.slice(0, MAX_BOXES * 3)
}