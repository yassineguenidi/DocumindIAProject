import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { getErrorMessage } from '../../utils/errors'
import { GOOGLE_CLIENT_ID, GoogleButton } from './GoogleButton'

export function GoogleAuth({ redirectTo, onError, text }: {
    redirectTo: string
    onError: (message: string) => void
    text: 'signin_with' | 'signup_with'
}) {
    const { loginWithGoogle } = useAuth()
    const navigate = useNavigate()
    const [busy, setBusy] = useState(false)

    if (!GOOGLE_CLIENT_ID) return null

    async function handle(credential: string) {
        if (busy) return
        setBusy(true)
        onError('')
        try {
            await loginWithGoogle(credential)
            navigate(redirectTo, { replace: true })
        } catch (e) {
            onError(getErrorMessage(e))
            setBusy(false)
        }
    }

    return (
        <div>
            <div className={busy ? 'pointer-events-none opacity-60 transition' : 'transition'} aria-busy={busy}>
                <GoogleButton onCredential={(c) => void handle(c)} text={text} />
            </div>
            <div className="my-6 flex items-center gap-3" role="separator">
                <span className="h-px flex-1" style={{ background: 'var(--border)' }} />
                <span className="muted text-xs font-semibold uppercase tracking-wider">ou avec votre email</span>
                <span className="h-px flex-1" style={{ background: 'var(--border)' }} />
            </div>
        </div>
    )
}