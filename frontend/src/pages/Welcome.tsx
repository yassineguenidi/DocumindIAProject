// provisoire elle devient dhasboard 
import { useNavigate } from 'react-router-dom'
import { LogOut, Moon, Sun } from 'lucide-react'
import { Logo } from '../components/Logo'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'

export default function Welcome() {
    const { user, logout } = useAuth()
    const { theme, toggle } = useTheme()
    const navigate = useNavigate()
    if (!user) return null

    return (
        <div className="bg-mesh grid min-h-screen place-items-center p-6">
            <div className="card glass shadow-soft w-full max-w-xl space-y-6 p-10 text-center">
                <div className="flex justify-center"><Logo /></div>
                <h1 className="text-4xl font-extrabold tracking-tight">
                    Bienvenue, <span className="text-gradient">{user.first_name}</span>
                </h1>
                <p className="muted">
                    {user.company_name} · offre <span className="font-semibold capitalize">{user.plan}</span>
                </p>
                <p className="muted text-sm">Votre espace de travail arrive à l'étape suivante.</p>
                <div className="flex justify-center gap-3">
                    <button onClick={toggle} className="btn-icon" aria-label="Changer de thème">
                        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                    </button>
                    <button onClick={() => { logout(); navigate('/') }} className="btn-ghost">
                        <LogOut size={18} /> Se déconnecter
                    </button>
                </div>
            </div>
        </div>
    )
}
