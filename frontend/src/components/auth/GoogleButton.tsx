import { useEffect, useRef, useState } from 'react'
import { useTheme } from '../../contexts/ThemeContext'

export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined

declare global {
    interface Window {
        google?: {
            accounts: {
                id: {
                    initialize: (cfg: { client_id: string; callback: (r: { credential: string }) => void }) => void
                    renderButton: (el: HTMLElement, opts: Record<string, unknown>) => void
                }
            }
        }
    }
}

let handler: ((credential: string) => void) | null = null
let initialized = false
let loader: Promise<void> | null = null

function loadGsi(): Promise<void> {
    if (window.google?.accounts?.id) return Promise.resolve()
    if (!loader) {
        loader = new Promise((resolve, reject) => {
            const s = document.createElement('script')
            s.src = 'https://accounts.google.com/gsi/client'
            s.async = true
            s.defer = true
            s.onload = () => resolve()
            s.onerror = () => { loader = null; reject(new Error('Google indisponible')) }
            document.head.appendChild(s)
        })
    }
    return loader
}

export function GoogleButton({ onCredential, text = 'signin_with' }: {
    onCredential: (credential: string) => void
    text?: 'signin_with' | 'signup_with'
}) {
    const ref = useRef<HTMLDivElement>(null)
    const { theme } = useTheme()
    const [failed, setFailed] = useState(false)

    useEffect(() => {
        handler = onCredential
        return () => { handler = null }
    }, [onCredential])

    useEffect(() => {
        if (!GOOGLE_CLIENT_ID) return
        let cancelled = false
        loadGsi()
            .then(() => {
                const el = ref.current
                if (cancelled || !el || !window.google) return
                if (!initialized) {
                    window.google.accounts.id.initialize({
                        client_id: GOOGLE_CLIENT_ID,
                        callback: (r) => handler?.(r.credential),
                    })
                    initialized = true
                }
                el.innerHTML = ''
                window.google.accounts.id.renderButton(el, {
                    type: 'standard',
                    theme: theme === 'dark' ? 'filled_black' : 'outline',
                    size: 'large',
                    shape: 'pill',
                    text,
                    locale: 'fr',
                    width: Math.min(400, Math.max(200, el.offsetWidth)),
                })
            })
            .catch(() => { if (!cancelled) setFailed(true) })
        return () => { cancelled = true }
    }, [theme, text])

    if (failed) return <p className="muted text-center text-sm">Connexion Google indisponible pour le moment.</p>
    return <div ref={ref} className="flex min-h-11 justify-center" />
}