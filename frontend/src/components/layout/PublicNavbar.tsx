import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Menu, Moon, Sun, X } from 'lucide-react'
import { Logo } from '../Logo'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'

const LINKS = [
    { href: '/#comment-ca-marche', label: 'Comment ça marche' },
    { href: '/#fonctionnalites', label: 'Fonctionnalités' },
    { href: '/#securite', label: 'Sécurité' },
    { href: '/#tarifs', label: 'Tarifs' },
    { href: '/#faq', label: 'FAQ' },
]

export function PublicNavbar() {
    const [open, setOpen] = useState(false)
    const { theme, toggle } = useTheme()
    const { user } = useAuth()

    return (
        <header className="glass sticky top-0 z-50 border-x-0 border-t-0">
            <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5" aria-label="Navigation principale">
                <Link to="/" aria-label="DocuMind AI, accueil"><Logo /></Link>

                <ul className="hidden items-center gap-8 lg:flex">
                    {LINKS.map((l) => (
                        <li key={l.href}>
                            <a href={l.href} className="muted text-sm font-semibold transition hover:text-[var(--text)]">{l.label}</a>
                        </li>
                    ))}
                </ul>

                <div className="flex items-center gap-2">
                    <button onClick={toggle} className="btn-icon" aria-label="Changer de thème">
                        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                    </button>
                    {user ? (
                        <Link to="/app" className="btn-primary hidden sm:inline-flex">Mon espace</Link>
                    ) : (
                        <>
                            <Link to="/login" className="btn-ghost hidden sm:inline-flex">Connexion</Link>
                            <Link to="/register" className="btn-primary hidden sm:inline-flex">Essayer gratuitement</Link>
                        </>
                    )}
                    <button className="btn-icon lg:hidden" onClick={() => setOpen(!open)} aria-label="Menu" aria-expanded={open}>
                        {open ? <X size={18} /> : <Menu size={18} />}
                    </button>
                </div>
            </nav>

            {open && (
                <div className="border-t px-5 pb-5 pt-3 lg:hidden" style={{ borderColor: 'var(--border)' }}>
                    <ul className="space-y-1">
                        {LINKS.map((l) => (
                            <li key={l.href}>
                                <a href={l.href} onClick={() => setOpen(false)} className="block rounded-xl px-3 py-2.5 font-semibold">{l.label}</a>
                            </li>
                        ))}
                    </ul>
                    {user ? (
                        <Link to="/app" className="btn-primary mt-3 w-full">Mon espace</Link>
                    ) : (
                        <div className="mt-3 grid grid-cols-2 gap-3">
                            <Link to="/login" className="btn-ghost">Connexion</Link>
                            <Link to="/register" className="btn-primary">Essayer</Link>
                        </div>
                    )}
                </div>
            )}
        </header>
    )
}