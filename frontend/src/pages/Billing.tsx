import { useEffect, useState } from 'react'
import { Check, Mail } from 'lucide-react'
import { QuotaRing } from '../components/dashboard/QuotaRing'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { Notice } from '../components/ui/Notice'
import { Reveal } from '../components/ui/Reveal'
import { useAuth } from '../contexts/AuthContext'
import { useUsage } from '../contexts/UsageContext'
import { CONTACT_EMAIL, PLAN_CATALOG, type PlanInfo } from '../data/plans'
import { cancelPlan, changePlan, fetchPlans } from '../services/billingService'
import type { Plan } from '../types'
import { getErrorMessage } from '../utils/errors'
import { parseApiDate } from '../utils/format'

import { usePageTitle } from '../hooks/usePageTitle'

type Target = { kind: 'change'; plan: PlanInfo } | { kind: 'cancel' }

function nextRenewal(periodStart: string): string {
    const d = parseApiDate(periodStart)
    const next = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1))
    return new Intl.DateTimeFormat('fr-FR', { dateStyle: 'long', timeZone: 'UTC' }).format(next)
}

const quotaText = (q: number | null) => (q === null ? 'Documents illimités' : `${q.toLocaleString('fr-FR')} documents / mois`)

export default function Billing() {
    const { user, refreshUser } = useAuth()
    const { usage, refreshUsage } = useUsage()
    const [plans, setPlans] = useState<Plan[]>([])
    const [target, setTarget] = useState<Target | null>(null)
    const [busy, setBusy] = useState(false)
    const [dialogError, setDialogError] = useState('')
    const [notice, setNotice] = useState('')

    useEffect(() => { fetchPlans().then(setPlans).catch(() => { /* on retombe sur le catalogue local */ }) }, [])

    if (!user) return null
    const isAdmin = user.role === 'admin'
    const currentIndex = PLAN_CATALOG.findIndex((p) => p.code === user.plan)
    const current = PLAN_CATALOG[currentIndex]
    const apiPlan = (code: string) => plans.find((p) => p.code === code)

    function open(t: Target) { setDialogError(''); setNotice(''); setTarget(t) }

    function dialog() {
        if (!target) return null
        if (target.kind === 'cancel') {
            const freeQuota = apiPlan('free')?.monthly_doc_quota
            return {
                title: "Résilier l'abonnement ?",
                message: `Votre compte repassera à l'offre Free${freeQuota != null ? ` (${quotaText(freeQuota)})` : ''}. Vos documents sont conservés. Mode démo : aucun paiement n'est concerné.`,
                confirmLabel: 'Résilier', tone: 'danger' as const,
            }
        }
        const newQuota = apiPlan(target.plan.code)?.monthly_doc_quota
        const over = usage && newQuota != null && usage.used >= newQuota
        return {
            title: `Passer à l'offre ${target.plan.name} ?`,
            message: `${current ? `Vous passez de l'offre ${current.name} à l'offre ${target.plan.name}. ` : ''}Mode démo : aucun paiement n'est effectué.${over ? ` Vous avez déjà traité ${usage.used} documents ce mois-ci : vous ne pourrez plus en ajouter avant le mois prochain.` : ''}`,
            confirmLabel: 'Confirmer', tone: over ? ('danger' as const) : ('primary' as const),
        }
    }

    async function apply() {
        if (!target) return
        setBusy(true)
        setDialogError('')
        try {
            if (target.kind === 'cancel') await cancelPlan()
            else await changePlan(target.plan.code)
            await Promise.all([refreshUser(), refreshUsage()])
            setNotice(target.kind === 'cancel' ? "Abonnement résilié : vous êtes revenu à l'offre Free." : `Vous êtes maintenant sur l'offre ${target.plan.name}.`)
            setTarget(null)
        } catch (e) {
            setDialogError(getErrorMessage(e))
        } finally {
            setBusy(false)
        }
    }

    const d = dialog()
    usePageTitle('Abonnement')
    return (
        <div className="space-y-6">
            <Reveal>
                <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Abonnement</h1>
                <p className="muted mt-1">Gérez votre offre et suivez votre consommation.</p>
            </Reveal>

            <Notice>Mode démo : aucun paiement n'est effectué, les changements d'offre sont simulés.</Notice>
            {notice && <Notice tone="success">{notice}</Notice>}
            {!isAdmin && <Notice>Seul un administrateur de votre entreprise peut modifier l'abonnement.</Notice>}

            <Reveal className="card grid items-center gap-6 p-6 sm:grid-cols-[auto_1fr] sm:p-8">
                {usage ? <QuotaRing used={usage.used} quota={usage.quota} /> : <div className="mx-auto h-44 w-44 animate-pulse rounded-full" style={{ background: 'var(--surface-2)' }} />}
                <div>
                    <p className="muted text-sm font-semibold">Offre actuelle</p>
                    <p className="text-gradient text-4xl font-extrabold tracking-tight">{current?.name ?? user.plan}</p>
                    {current && (
                        <p className="mt-1 text-lg font-semibold">
                            {current.price}{current.monthly && <span className="muted text-base"> / mois</span>}
                        </p>
                    )}
                    {usage && (
                        <p className="muted mt-3 text-sm">
                            {usage.max_file_size_mb} Mo max par fichier · le quota se renouvelle le {nextRenewal(usage.period_start)}.
                        </p>
                    )}
                    {isAdmin && user.plan !== 'free' && (
                        <button onClick={() => open({ kind: 'cancel' })} className="mt-5 text-sm font-semibold text-red-600 underline dark:text-red-400">
                            Résilier mon abonnement
                        </button>
                    )}
                </div>
            </Reveal>

            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
                {PLAN_CATALOG.map((p, i) => {
                    const api = apiPlan(p.code)
                    const isCurrent = p.code === user.plan
                    return (
                        <Reveal key={p.code} delay={i * 0.06}>
                            <div className={isCurrent ? 'bg-brand-gradient shadow-soft h-full rounded-[1.6rem] p-[2px]' : 'h-full'}>
                                <div className="card relative flex h-full flex-col p-6">
                                    {isCurrent && <span className="bg-brand-gradient absolute -top-3 left-6 rounded-full px-3 py-1 text-xs font-bold text-white">Offre actuelle</span>}
                                    <h2 className="text-lg font-bold">{p.name}</h2>
                                    <p className="mt-2 text-3xl font-extrabold tracking-tight">
                                        {p.price}{p.monthly && <span className="muted text-base font-semibold"> / mois</span>}
                                    </p>
                                    <p className="mt-3 font-semibold">{api ? quotaText(api.monthly_doc_quota) : p.quota}</p>
                                    <p className="muted text-sm">{api ? `${api.max_file_size_mb} Mo par fichier` : p.size}</p>
                                    <ul className="mt-4 flex-1 space-y-2 text-sm">
                                        {p.features.map((f) => (
                                            <li key={f} className="flex items-start gap-2"><Check size={16} className="mt-0.5 shrink-0 text-emerald-500" /> {f}</li>
                                        ))}
                                    </ul>
                                    {isCurrent ? (
                                        <button disabled className="btn-ghost mt-6 disabled:opacity-60">Offre actuelle</button>
                                    ) : p.code === 'enterprise' ? (
                                        <a href={`mailto:${CONTACT_EMAIL}?subject=Offre%20Enterprise`} className="btn-ghost mt-6"><Mail size={16} /> Nous contacter</a>
                                    ) : (
                                        <button
                                            disabled={!isAdmin}
                                            onClick={() => open({ kind: 'change', plan: p })}
                                            className={`${p.popular ? 'btn-primary' : 'btn-ghost'} mt-6 disabled:cursor-not-allowed disabled:opacity-60`}
                                        >
                                            {i > currentIndex ? `Passer à ${p.name}` : `Revenir à ${p.name}`}
                                        </button>
                                    )}
                                </div>
                            </div>
                        </Reveal>
                    )
                })}
            </div>

            {d && (
                <ConfirmDialog
                    title={d.title} message={d.message} confirmLabel={d.confirmLabel} tone={d.tone}
                    loading={busy} error={dialogError}
                    onConfirm={() => void apply()} onCancel={() => setTarget(null)}
                />
            )}
        </div>
    )
}