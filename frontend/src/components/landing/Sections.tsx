import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
    ArrowRight, Building2, Check, ChevronDown, Download, FileCheck2, Gauge, Layers,
    Lock, ScanText, Server, ShieldCheck, Sparkles, Trash2, Upload,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Reveal } from '../ui/Reveal'

import { PLAN_CATALOG } from '../../data/plans'

function Title({ eyebrow, children, sub }: { eyebrow: string; children: ReactNode; sub?: string }) {
    return (
        <Reveal className="mx-auto mb-14 max-w-2xl text-center">
            <span className="chip">{eyebrow}</span>
            <h2 className="mt-5 text-3xl font-extrabold tracking-tight sm:text-4xl lg:text-5xl">{children}</h2>
            {sub && <p className="muted mt-4 text-lg">{sub}</p>}
        </Reveal>
    )
}

function IconBox({ icon: Icon }: { icon: LucideIcon }) {
    return (
        <div className="bg-brand-gradient shadow-soft grid h-11 w-11 place-items-center rounded-xl text-white">
            <Icon size={22} />
        </div>
    )
}

/* ---------- Comment ça marche ---------- */
const STEPS = [
    { icon: Upload, title: 'Déposez', text: 'Glissez vos PDF ou images. DocuMind reconnaît le type de chaque document.' },
    { icon: ScanText, title: 'Lisez', text: "L'OCR récupère le texte, y compris sur des scans et des photos." },
    { icon: Sparkles, title: 'Extrayez', text: "L'IA identifie les informations clés et les structure automatiquement." },
    { icon: FileCheck2, title: 'Validez', text: 'Vérifiez en un coup d\'œil, puis exportez en JSON ou Excel.' },
]

export function HowItWorks() {
    return (
        <section id="comment-ca-marche" className="mx-auto max-w-7xl px-5 py-24">
            <Title eyebrow="Comment ça marche" sub="De la pile de documents aux données exploitables, en quatre étapes.">
                Simple comme <span className="text-gradient">1, 2, 3, 4</span>
            </Title>
            <ol className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
                {STEPS.map((s, i) => (
                    <Reveal key={s.title} delay={i * 0.08}>
                        <li className="card relative h-full p-6 transition hover:-translate-y-1 hover:shadow-[var(--shadow-soft)]">
                            <span className="text-gradient absolute right-5 top-4 text-5xl font-extrabold opacity-30">{i + 1}</span>
                            <IconBox icon={s.icon} />
                            <h3 className="mt-5 text-xl font-bold">{s.title}</h3>
                            <p className="muted mt-2 text-sm leading-relaxed">{s.text}</p>
                        </li>
                    </Reveal>
                ))}
            </ol>
        </section>
    )
}

/* ---------- Fonctionnalités (grille bento) ---------- */
const FEATURES: { icon: LucideIcon; title: string; text: string; span: string }[] = [
    { icon: Layers, title: 'Classification automatique', text: "Facture, contrat, CV, pièce d'identité : chaque document est identifié dès son arrivée, sans que vous ayez à le trier.", span: 'lg:col-span-2' },
    { icon: Sparkles, title: 'Extraction par IA', text: 'Fournisseur, montants, dates, compétences : les champs utiles sortent en données structurées.', span: '' },
    { icon: ScanText, title: 'OCR sur scans et photos', text: 'Documents numériques ou numérisés, DocuMind en lit le contenu.', span: '' },
    { icon: FileCheck2, title: 'Validation intelligente', text: 'Contrôles de cohérence automatiques (HT + TVA = TTC, dates, champs obligatoires) et relecture réservée aux cas douteux.', span: 'lg:col-span-2' },
    { icon: Download, title: 'Exports et intégrations', text: 'Récupérez vos données en JSON ou Excel. Connecteurs ERP et CRM à venir.', span: '' },
    { icon: Gauge, title: 'Quotas et suivi d\'usage', text: 'Suivez en temps réel votre consommation et choisissez l\'offre adaptée à votre volume de documents.', span: 'lg:col-span-2' },
]

export function Features() {
    return (
        <section id="fonctionnalites" className="bg-mesh">
            <div className="mx-auto max-w-7xl px-5 py-24">
                <Title eyebrow="Fonctionnalités" sub="Une plateforme complète de gestion documentaire, pas un simple OCR.">
                    Tout ce qu'il faut pour <span className="text-gradient">automatiser</span>
                </Title>
                <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                    {FEATURES.map((f, i) => (
                        <Reveal key={f.title} delay={(i % 3) * 0.08} className={f.span}>
                            <div className="card glass h-full p-7 transition hover:-translate-y-1 hover:shadow-[var(--shadow-soft)]">
                                <IconBox icon={f.icon} />
                                <h3 className="mt-5 text-xl font-bold">{f.title}</h3>
                                <p className="muted mt-2 leading-relaxed">{f.text}</p>
                            </div>
                        </Reveal>
                    ))}
                </div>
            </div>
        </section>
    )
}

/* ---------- Sécurité ---------- */
const SECURITY: { icon: LucideIcon; title: string; text: string; soon?: boolean }[] = [
    { icon: Building2, title: 'Données isolées', text: "Chaque entreprise accède uniquement à ses propres documents." },
    { icon: Lock, title: 'Accès protégé', text: 'Mots de passe hachés et sessions par jetons à durée limitée.' },
    { icon: Trash2, title: 'Vous gardez la main', text: 'Supprimez un document et son fichier à tout moment.' },
    { icon: Server, title: 'Déploiement on-premise', text: "Installation dans votre propre infrastructure, pour les données les plus sensibles.", soon: true },
]

export function Security() {
    return (
        <section id="securite" className="mx-auto grid max-w-7xl items-center gap-12 px-5 py-24 lg:grid-cols-[1fr_1.2fr]">
            <Reveal>
                <span className="chip"><ShieldCheck size={14} /> Sécurité et confidentialité</span>
                <h2 className="mt-5 text-3xl font-extrabold tracking-tight sm:text-4xl lg:text-5xl">
                    Vos documents sont <span className="text-gradient">les vôtres</span>
                </h2>
                <p className="muted mt-4 text-lg">
                    DocuMind est conçu pour les entreprises françaises, avec la confidentialité des données
                    et le RGPD comme point de départ.
                </p>
            </Reveal>
            <div className="grid gap-5 sm:grid-cols-2">
                {SECURITY.map((s, i) => (
                    <Reveal key={s.title} delay={i * 0.08}>
                        <div className="card h-full p-6">
                            <div className="flex items-start justify-between">
                                <IconBox icon={s.icon} />
                                {s.soon && <span className="chip">Bientôt</span>}
                            </div>
                            <h3 className="mt-4 text-lg font-bold">{s.title}</h3>
                            <p className="muted mt-1.5 text-sm leading-relaxed">{s.text}</p>
                        </div>
                    </Reveal>
                ))}
            </div>
        </section>
    )
}

/* ---------- Tarifs ---------- */
// // PRIX D'EXEMPLE : à remplacer par vos vrais tarifs.
// const PLANS = [
//     { name: 'Free', price: 'Gratuit', quota: '10 documents / mois', size: '5 Mo par fichier', features: ['Classification et extraction', 'Export JSON'] },
//     { name: 'Starter', price: '29 €', quota: '100 documents / mois', size: '10 Mo par fichier', features: ['Classification et extraction', 'Exports JSON et Excel'] },
//     { name: 'Business', price: '99 €', quota: '1 000 documents / mois', size: '25 Mo par fichier', features: ['Classification et extraction', 'Exports JSON et Excel', 'Validation avancée'], popular: true },
//     { name: 'Enterprise', price: 'Sur devis', quota: 'Documents illimités', size: '50 Mo par fichier', features: ['Intégrations ERP / CRM', 'On-premise (bientôt)', 'Accompagnement dédié'] },
// ]

export function Pricing() {
  return (
    <section id="tarifs" className="bg-mesh">
      <div className="mx-auto max-w-7xl px-5 py-24">
        <Title eyebrow="Tarifs" sub="Commencez gratuitement, changez d'offre quand votre volume augmente.">
          Une offre pour <span className="text-gradient">chaque taille</span> d'entreprise
        </Title>
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {PLAN_CATALOG.map((p, i) => (
            <Reveal key={p.code} delay={i * 0.08}>
              <div className={p.popular ? 'bg-brand-gradient shadow-soft h-full rounded-[1.6rem] p-[2px]' : 'h-full'}>
                <div className="card relative flex h-full flex-col p-7">
                  {p.popular && <span className="bg-brand-gradient absolute -top-3 left-7 rounded-full px-3 py-1 text-xs font-bold text-white">Populaire</span>}
                  <h3 className="text-lg font-bold">{p.name}</h3>
                  <p className="mt-3 text-4xl font-extrabold tracking-tight">
                    {p.price}
                    {p.monthly && <span className="muted text-base font-semibold"> / mois</span>}
                  </p>
                  <p className="mt-4 font-semibold">{p.quota}</p>
                  <p className="muted text-sm">{p.size}</p>
                  <ul className="mt-5 flex-1 space-y-2.5 text-sm">
                    {p.features.map((f) => (
                      <li key={f} className="flex items-start gap-2"><Check size={16} className="mt-0.5 shrink-0 text-emerald-500" /> {f}</li>
                    ))}
                  </ul>
                  <Link to="/register" className={`${p.popular ? 'btn-primary' : 'btn-ghost'} mt-7`}>
                    {p.code === 'enterprise' ? 'Nous contacter' : 'Commencer'}
                  </Link>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
/* ---------- FAQ ---------- */
const FAQ = [
    ['Quels formats de fichiers puis-je envoyer ?', 'Les PDF, PNG et JPG. Les documents numérisés et les photos sont lus grâce à l\'OCR.'],
    ['Mes documents sont-ils en sécurité ?', "Chaque entreprise n'accède qu'à ses propres documents, derrière une authentification. Vous pouvez supprimer un document et son fichier à tout moment."],
    ['Puis-je essayer gratuitement ?', "Oui. L'offre Free vous permet de traiter 10 documents par mois, sans carte bancaire."],
    ['Dois-je corriger les résultats à la main ?', "L'IA extrait les champs et signale les incohérences. Vous ne relisez que les cas douteux."],
    ['Puis-je changer ou arrêter mon offre ?', "À tout moment, depuis la page Abonnement de votre espace."],
]

export function Faq() {
    return (
        <section id="faq" className="mx-auto max-w-3xl px-5 py-24">
            <Title eyebrow="FAQ">Questions fréquentes</Title>
            <div className="space-y-3">
                {FAQ.map(([q, a]) => (
                    <details key={q} className="card group p-5">
                        <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-semibold">
                            {q}
                            <ChevronDown size={20} className="text-brand-500 shrink-0 transition group-open:rotate-180" />
                        </summary>
                        <p className="muted mt-3 leading-relaxed">{a}</p>
                    </details>
                ))}
            </div>
        </section>
    )
}

/* ---------- Appel à l'action final ---------- */
export function FinalCta() {
    return (
        <section className="mx-auto max-w-7xl px-5 pb-24">
            <Reveal>
                <div className="bg-brand-gradient shadow-soft relative overflow-hidden rounded-[2rem] px-8 py-16 text-center text-white">
                    <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-white/15 blur-3xl" />
                    <h2 className="relative text-3xl font-extrabold tracking-tight sm:text-5xl">
                        Arrêtez de saisir. Laissez DocuMind lire.
                    </h2>
                    <p className="relative mx-auto mt-4 max-w-xl text-lg text-white/85">
                        Créez votre compte gratuitement et traitez vos premiers documents en quelques minutes.
                    </p>
                    <Link to="/register" className="relative mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3.5 font-semibold text-brand-700 transition hover:-translate-y-0.5">
                        Créer mon compte <ArrowRight size={18} />
                    </Link>
                </div>
            </Reveal>
        </section>
    )
}