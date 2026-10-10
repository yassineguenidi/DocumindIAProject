import { api } from './api'

export async function downloadExport(path: string, params: Record<string, unknown>, filename: string): Promise<void> {
    const { data } = await api.get<Blob>(path, { params, responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export interface InboxInfo { enabled: boolean; address: string | null; allowed: string; require_auth: boolean }

export const fetchInbox = () => api.get<InboxInfo>('/company/inbox').then((r) => r.data)
export const saveInbox = (allowed: string) => api.put<InboxInfo>('/company/inbox', { allowed }).then((r) => r.data)
export const rotateInbox = () => api.post<InboxInfo>('/company/inbox/rotate').then((r) => r.data)