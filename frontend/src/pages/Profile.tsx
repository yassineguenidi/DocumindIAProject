import { useState, type FormEvent } from 'react'
import { LoaderCircle, Moon, Sun } from 'lucide-react'
import { ErrorAlert, Field, PasswordField, PasswordStrength } from '../components/ui/Field'
import { Notice } from '../components/ui/Notice'
import { Reveal } from '../components/ui/Reveal'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { changePassword, updateProfile } from '../services/profileService'
import type { User } from '../types'
import { getErrorMessage } from '../utils/errors'
import { passwordRules } from '../utils/password'
import { InboxCard } from '../components/settings/InboxCard'



const submitCls = 'btn-primary disabled:cursor-not-allowed disabled:opacity-60'

function PersonalInfo({ user }: { user: User }) {
    const { refreshUser } = useAuth()
    const isAdmin = user.role === 'admin'
    const [first, setFirst] = useState(user.first_name)
    const [last, setLast] = useState(user.last_name)
    const [company, setCompany] = useState(user.company_name)
    const [error, setError] = useState('')
    const [saved, setSaved] = useState(false)
    const [loading, setLoading] = useState(false)

    const dirty = first.trim() !== user.first_name || last.trim() !== user.last_name || (isAdmin && company.trim() !== user.company_name)

    async function onSubmit(e: FormEvent) {
        e.preventDefault()
        if (loading) return
        setError(''); setSaved(false)
        if (!first.trim() || !last.trim() || (isAdmin && !company.trim())) {
            setError('Tous les champs sont obligatoires')
            return
        }
        setLoading(true)
        try {
            await updateProfile({ first_name: first.trim(), last_name: last.trim(), ...(isAdmin ? { company_name: company.trim() } : {}) })
            await refreshUser()
            setSaved(true)
        } catch (err) {
            setError(getErrorMessage(err))
        } finally {
            setLoading(false)
        }
    }

    return (
        <form onSubmit={onSubmit} className="space-y-5" noValidate>
            <div className="grid gap-5 sm:grid-cols-2">
                <Field label="Prénom" autoComplete="given-name" value={first} onChange={(e) => setFirst(e.target.value)} />
                <Field label="Nom" autoComplete="family-name" value={last} onChange={(e) => setLast(e.target.value)} />
            </div>
            <div>
                <Field label="Email" type="email" value={user.email} disabled readOnly />
                <p className="muted mt-1.5 text-xs">L'adresse email n'est pas modifiable pour le moment.</p>
            </div>
            <Field label="Entreprise" autoComplete="organization" value={company} onChange={(e) => setCompany(e.target.value)} disabled={!isAdmin} />
            <ErrorAlert message={error} />
            {saved && !dirty && <Notice tone="success">Profil mis à jour.</Notice>}
            <button type="submit" disabled={!dirty || loading} className={submitCls}>
                {loading && <LoaderCircle size={18} className="animate-spin" />} Enregistrer
            </button>
        </form>
    )
}

function PasswordCard() {
    const [current, setCurrent] = useState('')
    const [next, setNext] = useState('')
    const [confirm, setConfirm] = useState('')
    const [errors, setErrors] = useState<Record<string, string>>({})
    const [serverError, setServerError] = useState('')
    const [success, setSuccess] = useState(false)
    const [loading, setLoading] = useState(false)

    async function onSubmit(e: FormEvent) {
        e.preventDefault()
        if (loading) return
        setServerError(''); setSuccess(false)
        const found: Record<string, string> = {}
        if (!current) found.current = 'Saisissez votre mot de passe actuel'
        if (!passwordRules.every((r) => r.test(next))) found.next = 'Le mot de passe ne respecte pas toutes les règles'
        else if (next === current) found.next = "Le nouveau mot de passe doit être différent de l'actuel"
        if (next !== confirm) found.confirm = 'Les mots de passe ne correspondent pas'
        setErrors(found)
        if (Object.keys(found).length) return

        setLoading(true)
        try {
            await changePassword(current, next)
            setCurrent(''); setNext(''); setConfirm('')
            setSuccess(true)
        } catch (err) {
            setServerError(getErrorMessage(err))
        } finally {
            setLoading(false)
        }
    }

    return (
        <form onSubmit={onSubmit} className="space-y-5" noValidate>
            <PasswordField label="Mot de passe actuel" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} error={errors.current} />
            <div>
                <PasswordField label="Nouveau mot de passe" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} error={errors.next} />
                <PasswordStrength password={next} />
            </div>
            <PasswordField label="Confirmer le nouveau mot de passe" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} error={errors.confirm} />
            <ErrorAlert message={serverError} />
            {success && <Notice tone="success">Mot de passe modifié.</Notice>}
            <button type="submit" disabled={loading} className={submitCls}>
                {loading && <LoaderCircle size={18} className="animate-spin" />} Changer le mot de passe
            </button>
        </form>
    )
}

function Appearance() {
    const { theme, toggle } = useTheme()
    const options = [
        { id: 'light' as const, label: 'Clair', icon: Sun },
        { id: 'dark' as const, label: 'Sombre', icon: Moon },
    ]
    return (
        <div role="group" aria-label="Thème de l'interface" className="grid max-w-sm grid-cols-2 gap-3">
            {options.map(({ id, label, icon: Icon }) => (
                <button
                    key={id} aria-pressed={theme === id}
                    onClick={() => { if (theme !== id) toggle() }}
                    className={`card flex items-center justify-center gap-2 py-4 font-semibold transition ${theme === id ? 'border-brand-500 ring-2 ring-brand-500/30' : 'muted'}`}
                >
                    <Icon size={18} /> {label}
                </button>
            ))}
        </div>
    )
}

export default function Profile() {
    const { user } = useAuth()
    if (!user) return null

    return (
        <div className="mx-auto max-w-3xl space-y-6">
            <Reveal>
                <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Profil</h1>
                <p className="muted mt-1">Vos informations, votre sécurité et vos préférences.</p>
            </Reveal>

            <Reveal className="card p-6 sm:p-8">
                <h2 className="mb-5 text-lg font-bold">Informations personnelles</h2>
                <PersonalInfo user={user} />
            </Reveal>

            <Reveal className="card p-6 sm:p-8">
                <h2 className="mb-5 text-lg font-bold">Mot de passe</h2>
                {user.has_password
                    ? <PasswordCard />
                    : <Notice>Votre compte utilise la connexion Google : il n'y a pas de mot de passe à gérer ici.</Notice>}
            </Reveal>

            <Reveal className="card p-6 sm:p-8">
                <h2 className="mb-5 text-lg font-bold">Apparence</h2>
                <Appearance />
            </Reveal>
            {user.role === 'admin' && (
                <Reveal className="card p-6 sm:p-8">
                    <h2 className="mb-5 text-lg font-bold">Réception par email</h2>
                    <InboxCard />
                </Reveal>
            )}
        </div>
    )
}