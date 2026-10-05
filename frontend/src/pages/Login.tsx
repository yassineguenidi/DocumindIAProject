import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { LoaderCircle } from 'lucide-react'
import { AuthLayout } from '../components/layout/AuthLayout'
import { ErrorAlert, Field, PasswordField } from '../components/ui/Field'
import { useAuth } from '../contexts/AuthContext'
import { getErrorMessage } from '../utils/errors'

import { usePageTitle } from '../hooks/usePageTitle'

import { GoogleAuth } from '../components/auth/GoogleAuth'

export default function Login() {
    const { login } = useAuth()
    const navigate = useNavigate()
    const location = useLocation()
    const from = (location.state as { from?: string } | null)?.from ?? '/app'

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    async function onSubmit(e: FormEvent) {
        e.preventDefault()
        if (loading) return
        setError('')
        setLoading(true)
        try {
            await login(email.trim(), password)
            navigate(from, { replace: true })
        } catch (err) {
            setError(getErrorMessage(err))
        } finally {
            setLoading(false)
        }
    }
    usePageTitle('Connexion')
    return (
        <AuthLayout
            title="Bon retour parmi nous"
            subtitle="Connectez-vous pour retrouver vos documents."
            footer={<>Pas encore de compte ? <Link to="/register" className="text-brand-500 font-semibold">Créer un compte</Link></>}
        >
            <GoogleAuth redirectTo={from} onError={setError} text="signin_with" />
            <form onSubmit={onSubmit} className="space-y-5" noValidate>
                <ErrorAlert message={error} />
                <Field label="Email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                <PasswordField label="Mot de passe" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                <button type="submit" disabled={loading || !email || !password} className="btn-primary w-full py-3.5 disabled:cursor-not-allowed disabled:opacity-60">
                    {loading && <LoaderCircle size={18} className="animate-spin" />} Se connecter
                </button>
            </form>
        </AuthLayout>
    )
}