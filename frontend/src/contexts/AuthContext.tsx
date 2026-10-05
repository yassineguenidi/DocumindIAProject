import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { fetchMe, loginRequest, registerRequest, googleLoginRequest } from '../services/authService'
import { tokenStorage } from '../services/tokenStorage'
import type { RegisterPayload, User } from '../types'

interface AuthState {
    user: User | null
    loading: boolean
    login: (email: string, password: string) => Promise<void>
    register: (payload: RegisterPayload) => Promise<void>
    logout: () => void
    refreshUser: () => Promise<void>
    loginWithGoogle: (credential: string) => Promise<void>
}


const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [loading, setLoading] = useState(() => tokenStorage.get() !== null)

    // Au chargement : si un token existe, on récupère le profil
    useEffect(() => {
        if (tokenStorage.get() === null) return
        let cancelled = false
        fetchMe()
            .then((u) => { if (!cancelled) setUser(u) })
            .catch(() => { /* 401 : l'intercepteur a déjà nettoyé ; autre erreur : on reste déconnecté */ })
            .finally(() => { if (!cancelled) setLoading(false) })
        return () => { cancelled = true }
    }, [])

    useEffect(() => {
        const onExpired = () => setUser(null)
        window.addEventListener('auth:expired', onExpired)
        return () => window.removeEventListener('auth:expired', onExpired)
    }, [])

    const login = useCallback(async (email: string, password: string) => {
        const token = await loginRequest(email, password)
        tokenStorage.set(token)
        try {
            setUser(await fetchMe())
        } catch (err) {
            tokenStorage.clear()
            throw err
        }
    }, [])

    const register = useCallback(async (payload: RegisterPayload) => {
        await registerRequest(payload)
        await login(payload.email, payload.password)
    }, [login])

    const logout = useCallback(() => {
        tokenStorage.clear()
        setUser(null)
    }, [])

    const refreshUser = useCallback(async () => { setUser(await fetchMe()) }, [])
    const loginWithGoogle = useCallback(async (credential: string) => {
        const token = await googleLoginRequest(credential)
        tokenStorage.set(token)
        setUser(await fetchMe())
    }, [])
    const value = useMemo(
        () => ({ user, loading, login, register, logout, refreshUser, loginWithGoogle }),
        [user, loading, login, register, logout, refreshUser, loginWithGoogle],
    )

    // const value = useMemo(() => ({ user, loading, login, register, logout }), [user, loading, login, register, logout])
    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth doit être utilisé dans AuthProvider')
    return ctx
}