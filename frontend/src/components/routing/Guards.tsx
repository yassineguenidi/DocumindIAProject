import { LoaderCircle } from 'lucide-react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export function FullScreenLoader() {
    return (
        <div className="grid min-h-screen place-items-center" role="status" aria-label="Chargement">
            <LoaderCircle className="text-brand-500 animate-spin" size={32} />
        </div>
    )
}

export function ProtectedRoute() {
    const { user, loading } = useAuth()
    const location = useLocation()
    if (loading) return <FullScreenLoader />
    if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
    return <Outlet />
}

export function GuestRoute() {
    const { user, loading } = useAuth()
    if (loading) return <FullScreenLoader />
    if (user) return <Navigate to="/app" replace />
    return <Outlet />
}