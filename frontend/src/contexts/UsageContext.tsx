import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { fetchUsage } from '../services/documentService'
import type { Usage } from '../types'

interface UsageState { usage: Usage | null; refreshUsage: () => Promise<void> }
const UsageContext = createContext<UsageState | null>(null)

export function UsageProvider({ children }: { children: ReactNode }) {
    const [usage, setUsage] = useState<Usage | null>(null)

    const refreshUsage = useCallback(async () => {
        try { setUsage(await fetchUsage()) } catch { /* l'affichage reste sur la dernière valeur */ }
    }, [])

    useEffect(() => { void refreshUsage() }, [refreshUsage])

    const value = useMemo(() => ({ usage, refreshUsage }), [usage, refreshUsage])
    return <UsageContext.Provider value={value}>{children}</UsageContext.Provider>
}

export function useUsage() {
    const ctx = useContext(UsageContext)
    if (!ctx) throw new Error('useUsage doit être utilisé dans UsageProvider')
    return ctx
}