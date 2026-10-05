import type { LucideIcon } from 'lucide-react'
import { AlertTriangle, CheckCircle2, Clock, FileStack } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ActivityChart } from '../components/dashboard/ActivityChart'
import { QuotaRing } from '../components/dashboard/QuotaRing'
import { RecentDocuments, SeeAll } from '../components/dashboard/RecentDocuments'
import { UploadZone } from '../components/documents/UploadZone'
import { Reveal } from '../components/ui/Reveal'
import { useAuth } from '../contexts/AuthContext'
import { useUsage } from '../contexts/UsageContext'
import { useDashboard } from '../hooks/useDashboard'

import { usePageTitle } from '../hooks/usePageTitle'



function StatCard({ icon: Icon, label, value, tone }: { icon: LucideIcon; label: string; value: number | string; tone: string }) {
    usePageTitle('Tableau de bord')
    return (
        <div className="card flex items-center gap-4 p-5">
            <div className={`grid h-12 w-12 shrink-0 place-items-center rounded-2xl ${tone}`}><Icon size={22} /></div>
            <div>
                <p className="muted text-sm font-semibold">{label}</p>
                <p className="text-3xl font-extrabold tracking-tight">{value}</p>
            </div>
        </div>
    )
}

export default function Dashboard() {
    const { user } = useAuth()
    const { usage } = useUsage()
    const { stats, recent, error, loading, reload } = useDashboard()
    if (!user) return null
    const v = (n?: number) => (loading || n === undefined ? '–' : n)

    return (
        <div className="space-y-6">
            <Reveal>
                <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
                    Bienvenue, <span className="text-gradient">{user.first_name}</span>
                </h1>
                <p className="muted mt-1">Voici l'état de vos documents.</p>
            </Reveal>

            {error && (
                <div role="alert" className="flex items-center justify-between gap-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">
                    {error}
                    <button onClick={() => void reload()} className="font-bold underline">Réessayer</button>
                </div>
            )}

            <Reveal className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard icon={FileStack} label="Documents" value={v(stats?.total)} tone="bg-brand-500/15 text-brand-600 dark:text-brand-300" />
                <StatCard icon={Clock} label="En cours" value={v(stats?.in_progress)} tone="bg-amber-500/15 text-amber-600 dark:text-amber-300" />
                <StatCard icon={CheckCircle2} label="Terminés" value={v(stats?.done)} tone="bg-emerald-500/15 text-emerald-600 dark:text-emerald-300" />
                <StatCard icon={AlertTriangle} label="Erreurs" value={v(stats?.failed)} tone="bg-red-500/15 text-red-600 dark:text-red-400" />
            </Reveal>

            <div className="grid gap-6 lg:grid-cols-3">
                <Reveal className="card p-6 lg:col-span-2">
                    <h2 className="text-lg font-bold">Activité</h2>
                    <p className="muted mb-4 text-sm">Documents envoyés sur les 14 derniers jours</p>
                    <ActivityChart data={stats?.activity ?? []} />
                </Reveal>

                <Reveal delay={0.08} className="card p-6">
                    <h2 className="text-lg font-bold">Votre quota</h2>
                    <p className="muted mb-4 text-sm capitalize">Offre {usage?.plan ?? user.plan}</p>
                    {usage ? <QuotaRing used={usage.used} quota={usage.quota} /> : <div className="mx-auto h-44 w-44 animate-pulse rounded-full" style={{ background: 'var(--surface-2)' }} />}
                    {usage && usage.remaining !== null && (
                        <p className="muted mt-4 text-center text-sm">
                            {usage.remaining > 0 ? `${usage.remaining} document${usage.remaining > 1 ? 's' : ''} restant${usage.remaining > 1 ? 's' : ''}` : 'Quota atteint'}
                            {' · '}<Link to="/app/billing" className="text-brand-500 font-semibold">Changer d'offre</Link>
                        </p>
                    )}
                </Reveal>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
                <Reveal className="card p-6 lg:col-span-2">
                    <div className="mb-2 flex items-center justify-between">
                        <h2 className="text-lg font-bold">Derniers documents</h2>
                        <SeeAll />
                    </div>
                    <RecentDocuments docs={recent} />
                </Reveal>

                <Reveal delay={0.08} className="card p-6">
                    <h2 className="mb-4 text-lg font-bold">Dépôt rapide</h2>
                    <UploadZone onUploaded={() => void reload()} />
                </Reveal>
            </div>
        </div>
    )
}