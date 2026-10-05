import type { ReactNode } from 'react'
import { Footer } from '../layout/Footer'
import { PublicNavbar } from '../layout/PublicNavbar'
import { Notice } from '../ui/Notice'
import { usePageTitle } from '../../hooks/usePageTitle'

// Passez à false une fois tous les champs [entre crochets] complétés et le texte relu par un juriste.
const DRAFT = true

export function Ph({ children }: { children: ReactNode }) {
    return <mark className="rounded bg-amber-400/30 px-1" style={{ color: 'var(--text)' }}>[{children}]</mark>
}

export function LegalSection({ title, children }: { title: string; children: ReactNode }) {
    return <section><h2>{title}</h2>{children}</section>
}

export function LegalLayout({ title, children }: { title: string; children: ReactNode }) {
    usePageTitle(title)
    return (
        <>
            <PublicNavbar />
            <main id="main" className="bg-mesh">
                <article className="mx-auto max-w-3xl px-5 py-16">
                    <h1 className="text-4xl font-extrabold tracking-tight">{title}</h1>
                    {DRAFT && (
                        <div className="mt-6">
                            <Notice>Modèle à compléter : renseignez les champs surlignés, faites relire le texte, puis passez DRAFT à false dans LegalLayout.tsx.</Notice>
                        </div>
                    )}
                    <div className="legal mt-10 space-y-8">{children}</div>
                </article>
            </main>
            <Footer />
        </>
    )
}