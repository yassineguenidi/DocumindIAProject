import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { CheckCircle2, CircleAlert, Info, X } from 'lucide-react'

type Tone = 'success' | 'error' | 'info'
interface ToastItem { id: number; tone: Tone; message: string }
interface ToastApi { success: (m: string) => void; error: (m: string) => void; info: (m: string) => void }

const ToastContext = createContext<ToastApi | null>(null)

const STYLE: Record<Tone, { icon: typeof Info; cls: string }> = {
    success: { icon: CheckCircle2, cls: 'text-emerald-500' },
    error: { icon: CircleAlert, cls: 'text-red-500' },
    info: { icon: Info, cls: 'text-brand-500' },
}

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<ToastItem[]>([])
    const nextId = useRef(0)

    const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), [])

    const push = useCallback((tone: Tone, message: string) => {
        const id = ++nextId.current
        setToasts((t) => [...t.slice(-3), { id, tone, message }])
        setTimeout(() => dismiss(id), tone === 'error' ? 7000 : 4000)
    }, [dismiss])

    const api = useMemo<ToastApi>(() => ({
        success: (m) => push('success', m),
        error: (m) => push('error', m),
        info: (m) => push('info', m),
    }), [push])

    // Session expirée (événement émis par l'intercepteur axios)
    useEffect(() => {
        const onExpired = () => push('info', 'Votre session a expiré. Reconnectez-vous.')
        window.addEventListener('auth:expired', onExpired)
        return () => window.removeEventListener('auth:expired', onExpired)
    }, [push])

    return (
        <ToastContext.Provider value={api}>
            {children}
            <div className="pointer-events-none fixed bottom-4 right-4 z-[70] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2" aria-live="polite">
                <AnimatePresence>
                    {toasts.map((t) => {
                        const { icon: Icon, cls } = STYLE[t.tone]
                        return (
                            <motion.div
                                key={t.id}
                                role={t.tone === 'error' ? 'alert' : 'status'}
                                initial={{ opacity: 0, y: 16 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, x: 40 }}
                                className="card glass shadow-soft pointer-events-auto flex items-start gap-3 px-4 py-3.5"
                            >
                                <Icon size={20} className={`mt-0.5 shrink-0 ${cls}`} />
                                <p className="flex-1 text-sm font-semibold">{t.message}</p>
                                <button onClick={() => dismiss(t.id)} className="muted shrink-0" aria-label="Fermer la notification"><X size={16} /></button>
                            </motion.div>
                        )
                    })}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    )
}

export function useToast() {
    const ctx = useContext(ToastContext)
    if (!ctx) throw new Error('useToast doit être utilisé dans ToastProvider')
    return ctx
}