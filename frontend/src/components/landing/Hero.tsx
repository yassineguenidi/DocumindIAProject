import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import {
    ArrowRight, Check, CheckCircle2, ClipboardList, Contact, FileSignature,
    FileText, FolderOpen, Receipt, Sparkles, User,
} from 'lucide-react'
import { Reveal } from '../ui/Reveal'

const FIELDS = [
    ['Fournisseur', 'Atelier Martin SAS'],
    ['N° de facture', 'FA-2026-0142'],
    ['Date', '12/09/2026'],
    ['Total HT', '1 070,00 €'],
    ['TVA 20 %', '214,00 €'],
    ['Total TTC', '1 284,00 €'],
]

const TYPES = [
    { icon: Receipt, label: 'Factures' },
    { icon: FileSignature, label: 'Contrats' },
    { icon: User, label: 'CV' },
    { icon: Contact, label: "Pièces d'identité" },
    { icon: ClipboardList, label: 'Formulaires' },
    { icon: FolderOpen, label: 'Dossiers clients' },
]

function HeroDemo() {
    return (
        <div className="relative">
            <div className="bg-brand-gradient absolute -inset-6 -z-10 rounded-[2rem] opacity-20 blur-3xl" />
            <motion.div
                className="card glass shadow-soft absolute -left-3 -top-5 z-10 hidden items-center gap-2 px-4 py-2 text-sm font-semibold sm:flex"
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
            >
                <Sparkles size={16} className="text-brand-500" /> Type détecté : Facture
            </motion.div>

            <div className="card glass shadow-soft p-5 sm:p-6">
                <div className="mb-4 flex items-center justify-between">
                    <span className="chip">Exemple</span>
                    <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 size={16} /> Validé
                    </span>
                </div>

                <div className="grid gap-4 sm:grid-cols-[1fr_auto_1.15fr] sm:items-center">
                    <div className="relative overflow-hidden rounded-2xl p-4" style={{ background: 'var(--surface-2)' }}>
                        <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
                            <FileText size={16} className="text-brand-500" /> facture.pdf
                        </div>
                        <div className="space-y-2.5 pb-4">
                            {[100, 70, 85, 55, 90, 40, 75].map((w, i) => (
                                <div key={i} className="h-2 rounded-full" style={{ width: `${w}%`, background: 'var(--border)' }} />
                            ))}
                        </div>
                        <motion.div
                            className="via-cyan-glow/30 pointer-events-none absolute inset-x-0 top-0 h-12 bg-gradient-to-b from-transparent to-transparent"
                            animate={{ y: [-48, 200] }}
                            transition={{ duration: 2.8, repeat: Infinity, ease: 'linear' }}
                        />
                    </div>

                    <ArrowRight className="text-brand-500 mx-auto rotate-90 sm:rotate-0" />

                    <ul className="space-y-2">
                        {FIELDS.map(([label, value], i) => (
                            <motion.li
                                key={label}
                                initial={{ opacity: 0, x: 16 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.5 + i * 0.12 }}
                                className="flex items-center justify-between gap-3 rounded-xl px-3 py-2 text-sm"
                                style={{ background: 'var(--surface-2)' }}
                            >
                                <span className="muted">{label}</span>
                                <span className="font-semibold">{value}</span>
                            </motion.li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    )
}

export function Hero() {
    return (
        <section className="bg-mesh relative overflow-hidden">
            <div className="mx-auto grid max-w-7xl items-center gap-16 px-5 pb-16 pt-16 lg:grid-cols-[1.05fr_1fr] lg:pt-24">
                <div>
                    <Reveal>
                        <span className="chip"><Sparkles size={14} /> Automatisation documentaire par IA</span>
                    </Reveal>
                    <Reveal delay={0.08}>
                        <h1 className="mt-6 text-5xl font-extrabold leading-[1.05] tracking-tight sm:text-6xl">
                            Vos documents deviennent <span className="text-gradient">des données</span>, sans saisie.
                        </h1>
                    </Reveal>
                    <Reveal delay={0.16}>
                        <p className="muted mt-6 max-w-xl text-lg">
                            Déposez vos factures, contrats ou CV. DocuMind les classe, lit leur contenu, en extrait
                            les informations clés et vous les livre prêtes à l'emploi.
                        </p>
                    </Reveal>
                    <Reveal delay={0.24} className="mt-9 flex flex-wrap gap-3">
                        <Link to="/register" className="btn-primary px-6 py-3.5">
                            Essayer gratuitement <ArrowRight size={18} />
                        </Link>
                        <a href="/#comment-ca-marche" className="btn-ghost px-6 py-3.5">Voir comment ça marche</a>
                    </Reveal>
                    <Reveal delay={0.32}>
                        <ul className="muted mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm font-semibold">
                            {['Pensé pour le RGPD', 'Gratuit pour démarrer', 'Sans carte bancaire'].map((t) => (
                                <li key={t} className="flex items-center gap-1.5"><Check size={16} className="text-emerald-500" /> {t}</li>
                            ))}
                        </ul>
                    </Reveal>
                </div>
                <Reveal delay={0.2}><HeroDemo /></Reveal>
            </div>

            <div className="mx-auto max-w-7xl px-5 pb-20">
                <p className="muted mb-5 text-center text-sm font-semibold uppercase tracking-wider">Tous vos documents métier</p>
                <ul className="flex flex-wrap justify-center gap-3">
                    {TYPES.map(({ icon: Icon, label }) => (
                        <li key={label} className="card flex items-center gap-2 px-4 py-2.5 text-sm font-semibold">
                            <Icon size={18} className="text-brand-500" /> {label}
                        </li>
                    ))}
                </ul>
            </div>
        </section>
    )
}