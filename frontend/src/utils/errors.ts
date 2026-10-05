import { isAxiosError } from 'axios'

export function getErrorMessage(err: unknown): string {
    if (isAxiosError(err)) {
        if (!err.response) return 'Impossible de joindre le serveur. Vérifiez votre connexion.'
        const detail = err.response.data?.detail
        if (typeof detail === 'string') return detail
        if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg).replace(/^Value error, /, '')
    }
    return 'Une erreur est survenue. Réessayez.'
}