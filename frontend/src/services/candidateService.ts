import { api } from './api'
import type { CandidateDetail, JobCriteria, MatchHit, SearchResponse, Supplier } from '../types'

export interface SearchParams {
    q: string
    minYears: string
    skills: string[]
    language: string
    location: string
    anonymous: boolean
}

export const searchCandidates = (p: SearchParams) =>
    api.get<SearchResponse>('/candidates/search', {
        params: {
            q: p.q || undefined, min_years: p.minYears || undefined, skills: p.skills,
            language: p.language || undefined, location: p.location || undefined, anonymous: p.anonymous,
        },
        paramsSerializer: { indexes: null }, // skills=a&skills=b
    }).then((r) => r.data)

export const reindexCandidates = () => api.post<{ queued: number }>('/candidates/reindex').then((r) => r.data)
export const parseJob = (text: string) => api.post<JobCriteria>('/candidates/job-criteria', { text }).then((r) => r.data)
export const matchCandidates = (criteria: JobCriteria, jobText: string, anonymous: boolean) =>
    api.post<MatchHit[]>('/candidates/match', { criteria, job_text: jobText, anonymous }).then((r) => r.data)
export const fetchCandidate = (id: number, anonymous: boolean) =>
    api.get<CandidateDetail>(`/candidates/${id}`, { params: { anonymous } }).then((r) => r.data)

export async function downloadCandidate(id: number, anonymous: boolean): Promise<void> {
    const { data } = await api.get<Blob>(`/candidates/${id}/export`, { params: { anonymous }, responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `dossier-candidat-${id}${anonymous ? '-anonyme' : ''}.docx`
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export const fetchSuppliers = () => api.get<Supplier[]>('/suppliers').then((r) => r.data)