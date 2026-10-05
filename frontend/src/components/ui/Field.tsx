import { useId, useState, type InputHTMLAttributes } from 'react'
import { Check, Circle, Eye, EyeOff } from 'lucide-react'
import { passwordRules, passwordStrength } from '../../utils/password'

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
    label: string
    error?: string
}

export function Field({ label, error, ...props }: FieldProps) {
    const id = useId()
    return (
        <div>
            <label htmlFor={id} className="mb-1.5 block text-sm font-semibold">{label}</label>
            <input
                id={id}
                className="input"
                aria-invalid={!!error}
                aria-describedby={error ? `${id}-err` : undefined}
                {...props}
            />
            {error && <p id={`${id}-err`} className="mt-1.5 text-sm text-red-500">{error}</p>}
        </div>
    )
}

export function PasswordField({ label, error, ...props }: FieldProps) {
    const id = useId()
    const [show, setShow] = useState(false)
    return (
        <div>
            <label htmlFor={id} className="mb-1.5 block text-sm font-semibold">{label}</label>
            <div className="relative">
                <input
                    id={id}
                    className="input pr-12"
                    maxLength={72}
                    aria-invalid={!!error}
                    aria-describedby={error ? `${id}-err` : undefined}
                    {...props}
                    type={show ? 'text' : 'password'}
                />
                <button
                    type="button"
                    onClick={() => setShow(!show)}
                    className="muted absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-2 transition hover:text-[var(--text)]"
                    aria-label={show ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                    aria-pressed={show}
                >
                    {show ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
            </div>
            {error && <p id={`${id}-err`} className="mt-1.5 text-sm text-red-500">{error}</p>}
        </div>
    )
}

export function PasswordStrength({ password }: { password: string }) {
    const { score, label } = passwordStrength(password)
    const colors = ['bg-red-500', 'bg-orange-500', 'bg-brand-400', 'bg-emerald-500']
    return (
        <div className="mt-3" aria-live="polite">
            <div className="flex gap-1.5">
                {[0, 1, 2, 3].map((i) => (
                    <div
                        key={i}
                        className={`h-1.5 flex-1 rounded-full transition-colors ${i < score ? colors[score - 1] : ''}`}
                        style={i >= score ? { background: 'var(--border)' } : undefined}
                    />
                ))}
            </div>
            <p className="muted mt-1.5 h-4 text-xs font-semibold">{password ? `Robustesse : ${label}` : ''}</p>
            <ul className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
                {passwordRules.map((r) => {
                    const ok = r.test(password)
                    return (
                        <li key={r.id} className={`flex items-center gap-1.5 ${ok ? 'text-emerald-600 dark:text-emerald-400' : 'muted'}`}>
                            {ok ? <Check size={14} /> : <Circle size={14} />} {r.label}
                        </li>
                    )
                })}
            </ul>
        </div>
    )
}

export function ErrorAlert({ message }: { message: string }) {
    if (!message) return null
    return (
        <div role="alert" className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">
            {message}
        </div>
    )
}