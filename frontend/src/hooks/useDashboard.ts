import { useCallback, useEffect, useState } from 'react'
import { fetchStats, listDocuments } from '../services/documentService'
import type { DocumentItem, Stats } from '../types'
import { getErrorMessage } from '../utils/errors'

export function useDashboard() {
    const [stats, setStats] = useState<Stats | null>(null)
    const [recent, setRecent] = useState<DocumentItem[]>([])
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(true)

    const load = useCallback(async () => {
        try {
            const [s, l] = await Promise.all([fetchStats(), listDocuments(0, 5)])
            setStats(s)
            setRecent(l.items)
            setError('')
        } catch (e) {
            setError(getErrorMessage(e))
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => { void load() }, [load])
    return { stats, recent, error, loading, reload: load }
}
