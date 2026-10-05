import { api } from './api'
import type { DocumentItem, DocumentList, Stats, Usage } from '../types'

export async function uploadDocument(file: File, onProgress?: (pct: number) => void): Promise<DocumentItem> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post<DocumentItem>('/documents/upload', form, {
        onUploadProgress: (e) => {
            if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
        },
    })
    return data
}

// export const listDocuments = (skip = 0, limit = 20) =>
//     api.get<DocumentList>('/documents', { params: { skip, limit } }).then((r) => r.data)

export const listDocuments = (
    skip = 0,
    limit = 20,
    filters: { q?: string; status?: string } = {},
) =>
    api
        .get<DocumentList>('/documents', {
            params: { skip, limit, q: filters.q || undefined, status: filters.status },
        })
        .then((r) => r.data)

export async function downloadDocument(id: number, filename: string): Promise<void> {
    // Le fichier est protégé par le token : on le récupère via axios puis on le sauvegarde
    const { data } = await api.get<Blob>(`/documents/${id}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export const fetchUsage = () => api.get<Usage>('/documents/usage').then((r) => r.data)
export const fetchStats = () => api.get<Stats>('/documents/stats').then((r) => r.data)
export const deleteDocument = (id: number) => api.delete(`/documents/${id}`)