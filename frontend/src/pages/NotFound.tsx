import { Link } from 'react-router-dom'
import { Footer } from '../components/layout/Footer'
import { PublicNavbar } from '../components/layout/PublicNavbar'
import { usePageTitle } from '../hooks/usePageTitle'

// usePageTitle('Page introuvable')

export default function NotFound({ inApp = false }: { inApp?: boolean }) {
    usePageTitle('Page introuvable')

    const content = (
        <div className="mx-auto max-w-lg px-5 py-24 text-center">
            <p className="text-gradient text-8xl font-extrabold tracking-tight">404</p>
            <h1 className="mt-4 text-2xl font-extrabold">Page introuvable</h1>
            <p className="muted mt-2">La page que vous cherchez n'existe pas ou a été déplacée.</p>
            <Link to={inApp ? '/app' : '/'} className="btn-primary mt-8">
                {inApp ? 'Retour au tableau de bord' : "Retour à l'accueil"}
            </Link>
        </div>
    )

    if (inApp) return content
    return (
        <>
            <PublicNavbar />
            <main id="main" className="bg-mesh">{content}</main>
            <Footer />
        </>
    )
}