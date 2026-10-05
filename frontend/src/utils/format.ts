// Le backend renvoie des dates UTC, parfois sans fuseau : on force "Z"
export function parseApiDate(s: string): Date {
    return new Date(/[zZ]$|[+-]\d\d:?\d\d$/.test(s) ? s : `${s}Z`)
}

export function formatDateTime(s: string): string {
    return new Intl.DateTimeFormat('fr-FR', {
        day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
    }).format(parseApiDate(s))
}

export function formatBytes(n: number): string {
    if (n < 1024) return `${n} o`
    if (n < 1024 ** 2) return `${Math.round(n / 1024)} Ko`
    return `${(n / 1024 ** 2).toFixed(1)} Mo`
}


export function formatDateFull(s: string): string {
    return new Intl.DateTimeFormat('fr-FR', { dateStyle: 'long', timeStyle: 'short' }).format(parseApiDate(s))
}

const DOC_TYPES: Record<string, string> = {
    invoice: 'Facture', contract: 'Contrat', cv: 'CV', id: "Pièce d'identité", other: 'Autre',
}

export function docTypeLabel(t: string | null): string {
    return t ? (DOC_TYPES[t] ?? t) : '—'
}