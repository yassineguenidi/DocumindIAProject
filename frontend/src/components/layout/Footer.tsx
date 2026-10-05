import { Link } from 'react-router-dom'
import { Logo } from '../Logo'

export function Footer() {
    return (
        <footer className="border-t" style={{ borderColor: 'var(--border)' }}>
            <div className="mx-auto grid max-w-7xl gap-10 px-5 py-14 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
                <div className="space-y-4">
                    <Logo />
                    <p className="muted max-w-sm text-sm">L'automatisation documentaire par IA, pensée pour les PME françaises.</p>
                </div>
                <div>
                    <h3 className="mb-3 text-sm font-bold">Produit</h3>
                    <ul className="muted space-y-2 text-sm">
                        <li><a href="/#fonctionnalites">Fonctionnalités</a></li>
                        <li><a href="/#tarifs">Tarifs</a></li>
                        <li><a href="/#faq">FAQ</a></li>
                    </ul>
                </div>
                <div>
                    <h3 className="mb-3 text-sm font-bold">Compte</h3>
                    <ul className="muted space-y-2 text-sm">
                        <li><Link to="/login">Connexion</Link></li>
                        <li><Link to="/register">Créer un compte</Link></li>
                    </ul>
                </div>
                <div>
                    <h3 className="mb-3 text-sm font-bold">Légal</h3>
                    <ul className="muted space-y-2 text-sm">
                        <li><Link to="/mentions-legales">Mentions légales</Link></li>
                        <li><Link to="/confidentialite">Confidentialité</Link></li>
                    </ul>
                </div>
            </div>
            <div className="border-t py-5 text-center text-sm muted" style={{ borderColor: 'var(--border)' }}>
                © {new Date().getFullYear()} DocuMind AI. Tous droits réservés.
            </div>
        </footer>
    )
}