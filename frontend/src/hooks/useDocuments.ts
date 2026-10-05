import { useCallback, useEffect, useRef, useState } from 'react'
import { listDocuments } from '../services/documentService'
import type { DocumentItem, StatusFilter } from '../types'
import { getErrorMessage } from '../utils/errors'
import { useDebounce } from './useDebounce'

export const PAGE_SIZE = 10
const ACTIVE = ['uploading', 'queued', 'ocr', 'extraction', 'validation']

export function useDocuments() {
  const [items, setItems] = useState<DocumentItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [search, setSearchState] = useState('')
  const [status, setStatusState] = useState<StatusFilter>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const q = useDebounce(search.trim(), 300)
  const requestId = useRef(0)

  const load = useCallback(async (silent = false) => {
    const id = ++requestId.current
    if (!silent) setLoading(true)
    try {
      const data = await listDocuments(page * PAGE_SIZE, PAGE_SIZE, {
        q,
        status: status === 'all' ? undefined : status,
      })
      if (id !== requestId.current) return
      if (data.items.length === 0 && data.total > 0 && page > 0) {
        setPage(Math.ceil(data.total / PAGE_SIZE) - 1)
        return
      }
      setItems(data.items)
      setTotal(data.total)
      setError('')
    } catch (e) {
      if (id === requestId.current && !silent) setError(getErrorMessage(e))
    } finally {
      if (id === requestId.current) setLoading(false)
    }
  }, [page, q, status])

  useEffect(() => { void load() }, [load])

  // Tant qu'un document est en cours de traitement, on rafraîchit toutes les 3 secondes
  const hasActive = items.some((d) => ACTIVE.includes(d.status))
  useEffect(() => {
    if (!hasActive) return
    const t = setInterval(() => { void load(true) }, 3000)
    return () => clearInterval(t)
  }, [hasActive, load])

  const setSearch = (v: string) => { setSearchState(v); setPage(0) }
  const setStatus = (v: StatusFilter) => { setStatusState(v); setPage(0) }
  const resetFilters = () => { setSearchState(''); setStatusState('all'); setPage(0) }

  return { items, total, page, setPage, search, setSearch, status, setStatus, resetFilters, loading, error, reload: load }
}