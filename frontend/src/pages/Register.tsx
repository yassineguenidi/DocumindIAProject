import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LoaderCircle } from 'lucide-react'
import { AuthLayout } from '../components/layout/AuthLayout'
import { ErrorAlert, Field, PasswordField, PasswordStrength } from '../components/ui/Field'
import { useAuth } from '../contexts/AuthContext'
import { getErrorMessage } from '../utils/errors'
import { passwordRules } from '../utils/password'

import { GoogleAuth } from '../components/auth/GoogleAuth'

const EMPTY = { first_name: '', last_name: '', company_name: '', email: '', password: '', confirm: '' }

function validate(f: typeof EMPTY) {
    const e: Record<string, string> = {}
    if (!f.first_name.trim()) e.first_name = 'Prénom requis'
    if (!f.last_name.trim()) e.last_name = 'Nom requis'
    if (!f.company_name.trim()) e.company_name = "Nom de l'entreprise requis"
    if (!/^\S+@\S+\.\S+$/.test(f.email.trim())) e.email = 'Adresse email invalide'
    if (!passwordRules.every((r) => r.test(f.password))) e.password = 'Le mot de passe ne respecte pas toutes les règles'
    if (f.password !== f.confirm) e.confirm = 'Les mots de passe ne correspondent pas'
    return e
}

export default function Register() {
    const { register } = useAuth()
    const navigate = useNavigate()
    const [form, setForm] = useState(EMPTY)
    const [errors, setErrors] = useState<Record<string, string>>({})
    const [serverError, setServerError] = useState('')
    const [loading, setLoading] = useState(false)

    const set = (key: keyof typeof EMPTY) => (e: React.ChangeEvent<HTMLInputElement>) =>
        setForm((f) => ({ ...f, [key]: e.target.value }))

    async function onSubmit(e: FormEvent) {
        e.preventDefault()
        if (loading) return
        setServerError('')
        const found = validate(form)
        setErrors(found)
        if (Object.keys(found).length) return

        setLoading(true)
        try {
            await register({
                first_name: form.first_name.trim(),
                last_name: form.last_name.trim(),
                company_name: form.company_name.trim(),
                email: form.email.trim(),
                password: form.password,
            })
            navigate('/app', { replace: true })
        } catch (err) {
            setServerError(getErrorMessage(err))
        } finally {
            setLoading(false)
        }
    }

    return (
        <AuthLayout
            title="Créez votre compte"
            subtitle="Gratuit pour démarrer, sans carte bancaire."
            footer={<>Déjà inscrit ? <Link to="/login" className="text-brand-500 font-semibold">Se connecter</Link></>}
        >
            <GoogleAuth redirectTo="/app" onError={setServerError} text="signup_with" />
            <form onSubmit={onSubmit} className="space-y-5" noValidate>
                <ErrorAlert message={serverError} />
                <div className="grid gap-5 sm:grid-cols-2">
                    <Field label="Prénom" autoComplete="given-name" value={form.first_name} onChange={set('first_name')} error={errors.first_name} />
                    <Field label="Nom" autoComplete="family-name" value={form.last_name} onChange={set('last_name')} error={errors.last_name} />
                </div>
                <Field label="Entreprise" autoComplete="organization" value={form.company_name} onChange={set('company_name')} error={errors.company_name} />
                <Field label="Email professionnel" type="email" autoComplete="email" value={form.email} onChange={set('email')} error={errors.email} />
                <div>
                    <PasswordField label="Mot de passe" autoComplete="new-password" value={form.password} onChange={set('password')} error={errors.password} />
                    <PasswordStrength password={form.password} />
                </div>
                <PasswordField label="Confirmer le mot de passe" autoComplete="new-password" value={form.confirm} onChange={set('confirm')} error={errors.confirm} />
                <p className="muted text-xs">
                    En créant un compte, vous reconnaissez avoir pris connaissance de notre{' '}
                    <Link to="/confidentialite" className="text-brand-500 font-semibold underline">politique de confidentialité</Link>.
                </p>
                <button type="submit" disabled={loading} className="btn-primary w-full py-3.5 disabled:cursor-not-allowed disabled:opacity-60">
                    {loading && <LoaderCircle size={18} className="animate-spin" />} Créer mon compte
                </button>
            </form>
        </AuthLayout>
    )
}