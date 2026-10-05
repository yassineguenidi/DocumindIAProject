import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Building2, CreditCard, FileText, LayoutDashboard, LogOut, Menu, Moon, Sun, User as UserIcon, X } from 'lucide-react'
import { Logo } from '../Logo'
import { useAuth } from '../../contexts/AuthContext'
import { useTheme } from '../../contexts/ThemeContext'
import { UsageProvider, useUsage } from '../../contexts/UsageContext'

const NAV = [
    { to: '/app', label: 'Tableau de bord', icon: LayoutDashboard, end: true },
    { to: '/app/documents', label: 'Documents', icon: FileText, end: false },
    { to: '/app/billing', label: 'Abonnement', icon: CreditCard, end: false },
    { to: '/app/profile', label: 'Profil', icon: UserIcon, end: false },
]

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
    const { usage } = useUsage()
    const pct = usage?.quota ? Math.min(100, (usage.used / usage.quota) * 100) : 100

    return (
        <div className="flex h-full flex-col p-4">
            <Link to="/" onClick={onNavigate} className="px-2 py-3" aria-label="Retour au site"><Logo /></Link>
            <nav className="mt-6 flex-1 space-y-1" aria-label="Navigation de l'application">
                {NAV.map(({ to, label, icon: Icon, end }) => (
                    <NavLink
                        key={to} to={to} end={end} onClick={onNavigate}
                        className={({ isActive }) =>
                            `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition ${isActive ? 'bg-brand-gradient shadow-soft text-white' : 'muted hover:bg-[var(--surface-2)] hover:text-[var(--text)]'
                            }`
                        }
                    >
                        <Icon size={19} /> {label}
                    </NavLink>
                ))}
            </nav>
            {usage && (
                <Link to="/app/billing" onClick={onNavigate} className="card block p-4">
                    <div className="flex items-center justify-between text-sm">
                        <span className="font-bold capitalize">{usage.plan}</span>
                        <span className="muted">{usage.quota === null ? 'Illimité' : `${usage.used} / ${usage.quota}`}</span>
                    </div>
                    <div className="mt-3 h-2 overflow-hidden rounded-full" style={{ background: 'var(--surface-2)' }}>
                        <div className="bg-brand-gradient h-full rounded-full transition-all" style={{ width: `${pct}%` }} />
                    </div>
                    <p className="text-brand-500 mt-3 text-xs font-semibold">Gérer mon abonnement</p>
                </Link>
            )}
        </div>
    )
}

function Topbar({ onMenu }: { onMenu: () => void }) {
    const { user, logout } = useAuth()
    const { theme, toggle } = useTheme()
    const navigate = useNavigate()
    const [menu, setMenu] = useState(false)
    const ref = useRef<HTMLDivElement>(null)

    useEffect(() => {
        const onDown = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) setMenu(false)
        }
        document.addEventListener('mousedown', onDown)
        return () => document.removeEventListener('mousedown', onDown)
    }, [])

    if (!user) return null
    const initials = `${user.first_name[0] ?? ''}${user.last_name[0] ?? ''}`.toUpperCase()

    return (
        <header className="glass sticky top-0 z-20 flex h-16 items-center justify-between border-x-0 border-t-0 px-5 sm:px-8">
            <div className="flex items-center gap-3">
                <button className="btn-icon lg:hidden" onClick={onMenu} aria-label="Ouvrir le menu"><Menu size={18} /></button>
                <p className="muted hidden items-center gap-2 text-sm font-semibold sm:flex">
                    <Building2 size={16} /> {user.company_name}
                </p>
            </div>
            <div className="flex items-center gap-2">
                <button onClick={toggle} className="btn-icon" aria-label="Changer de thème">
                    {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                </button>
                <div className="relative" ref={ref}>
                    <button
                        onClick={() => setMenu(!menu)}
                        className="bg-brand-gradient grid h-10 w-10 place-items-center rounded-full text-sm font-bold text-white"
                        aria-label="Menu du compte" aria-expanded={menu}
                    >
                        {initials}
                    </button>
                    {menu && (
                        <div className="card shadow-soft absolute right-0 z-50 mt-2 w-64 p-2">
                            <div className="px-3 py-2">
                                <p className="font-bold">{user.first_name} {user.last_name}</p>
                                <p className="muted truncate text-sm">{user.email}</p>
                            </div>
                            <hr style={{ borderColor: 'var(--border)' }} />
                            <Link to="/app/profile" onClick={() => setMenu(false)} className="mt-1 flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold hover:bg-[var(--surface-2)]">
                                <UserIcon size={16} /> Mon profil
                            </Link>
                            <button
                                onClick={() => { logout(); navigate('/') }}
                                className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold hover:bg-[var(--surface-2)]"
                            >
                                <LogOut size={16} /> Se déconnecter
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </header>
    )
}

function Shell() {
    const [open, setOpen] = useState(false)

    useEffect(() => {
        const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
        window.addEventListener('keydown', onKey)
        return () => window.removeEventListener('keydown', onKey)
    }, [])

    const panel = { background: 'var(--surface)', borderColor: 'var(--border)' }
    return (
        <div className="min-h-screen">
            <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r lg:block" style={panel}>
                <SidebarContent />
            </aside>

            {open && (
                <div className="fixed inset-0 z-40 lg:hidden">
                    <div className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} />
                    <aside className="absolute inset-y-0 left-0 w-72 border-r" style={panel}>
                        <button className="btn-icon absolute right-3 top-4" onClick={() => setOpen(false)} aria-label="Fermer le menu"><X size={18} /></button>
                        <SidebarContent onNavigate={() => setOpen(false)} />
                    </aside>
                </div>
            )}

            <div className="lg:pl-64">
                <Topbar onMenu={() => setOpen(true)} />
                <main className="mx-auto max-w-7xl p-5 sm:p-8"><Outlet /></main>
            </div>
        </div>
    )
}

export default function AppLayout() {
    return (
        <UsageProvider>
            <Shell />
        </UsageProvider>
    )
}