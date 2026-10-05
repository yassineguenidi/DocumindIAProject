import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Check, Moon, Sun } from 'lucide-react'
import { Logo } from '../Logo'
import { useTheme } from '../../contexts/ThemeContext'

const POINTS = ['Classification automatique', 'Extraction par IA', 'Exports JSON et Excel', 'Pensé pour le RGPD']

export function AuthLayout({ title, subtitle, children, footer }: {
    title: string; subtitle: string; children: ReactNode; footer: ReactNode
}) {
    const { theme, toggle } = useTheme()
    return (
        <div className="grid min-h-screen lg:grid-cols-2">
            <div className="flex flex-col px-6 py-6 sm:px-12">
                <div className="flex items-center justify-between">
                    <Link to="/" aria-label="DocuMind AI, accueil"><Logo /></Link>
                    <button onClick={toggle} className="btn-icon" aria-label="Changer de thème">
                        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                    </button>
                </div>
                <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-10">
                    <h1 className="text-3xl font-extrabold tracking-tight">{title}</h1>
                    <p className="muted mt-2">{subtitle}</p>
                    <div className="mt-8">{children}</div>
                    <p className="muted mt-8 text-center text-sm">{footer}</p>
                </main>
            </div>

            <aside className="bg-brand-gradient relative hidden flex-col justify-center overflow-hidden p-14 text-white lg:flex" aria-hidden="true">
                <div className="absolute -right-24 -top-24 h-96 w-96 rounded-full bg-white/15 blur-3xl" />
                <div className="absolute -bottom-32 -left-20 h-96 w-96 rounded-full bg-cyan-300/25 blur-3xl" />
                <div className="relative max-w-md">
                    <h2 className="text-4xl font-extrabold leading-tight tracking-tight">Vos documents, transformés en données.</h2>
                    <p className="mt-4 text-lg text-white/85">Déposez, laissez DocuMind lire, validez. Fini la saisie manuelle.</p>
                    <ul className="mt-8 space-y-3">
                        {POINTS.map((p) => (
                            <li key={p} className="flex items-center gap-3 font-semibold">
                                <span className="grid h-6 w-6 place-items-center rounded-full bg-white/20"><Check size={14} /></span>
                                {p}
                            </li>
                        ))}
                    </ul>
                </div>
            </aside>
        </div>
    )
}