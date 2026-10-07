import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, CircleHelp, Download, EyeOff, FileSearch, LoaderCircle, RefreshCw, Search, Sparkles, X, XCircle } from 'lucide-react'
import { Notice } from '../components/ui/Notice'
import { useToast } from '../contexts/ToastContext'
import { JOB_FAMILIES } from '../data/jobFamilies'
import { useDebounce } from '../hooks/useDebounce'
import { usePageTitle } from '../hooks/usePageTitle'
import {
    downloadCandidate, fetchCandidate, matchCandidates, parseJob, reindexCandidates, searchCandidates,
} from '../services/candidateService'
import type { CandidateDetail, CandidateHit, CriterionResult, JobCriteria, MatchHit, SearchResponse } from '../types'
import { getErrorMessage } from '../utils/errors'

const chip = 'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold'

function ChipInput({ label, values, onChange, placeholder }: {
    label: string; values: string[]; onChange: (v: string[]) => void; placeholder?: string
}) {
    const [text, setText] = useState('')
    const add = () => {
        const v = text.trim()
        if (v && !values.includes(v)) onChange([...values, v])
        setText('')
    }
    const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); add() }
        else if (e.key === 'Backspace' && !text && values.length) onChange(values.slice(0, -1))
    }
    return (
        <div>
            <label className="mb-1.5 block text-sm font-semibold">{label}</label>
            <div className="flex flex-wrap items-center gap-1.5 rounded-[.9rem] border px-3 py-2" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                {values.map((v) => (
                    <span key={v} className={`${chip} bg-brand-500/15 text-brand-600 dark:text-brand-300`}>
                        {v}
                        <button type="button" onClick={() => onChange(values.filter((x) => x !== v))} aria-label={`Retirer ${v}`}><X size={12} /></button>
                    </span>
                ))}
                <input
                    value={text} onChange={(e) => setText(e.target.value)} onKeyDown={onKey} onBlur={add}
                    placeholder={values.length ? '' : placeholder} aria-label={label}
                    className="min-w-[8rem] flex-1 bg-transparent py-1 text-sm outline-none"
                />
            </div>
        </div>
    )
}

function CandidateCard({ hit, onOpen, children }: { hit: CandidateHit; onOpen: () => void; children?: ReactNode }) {
    const meta = [hit.location, `${hit.years} an${hit.years >= 2 ? 's' : ''}`, hit.job_family && JOB_FAMILIES[hit.job_family]].filter(Boolean).join(' · ')
    return (
        <div className="card p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <button onClick={onOpen} className="min-w-0 text-left">
                    <p className="truncate text-lg font-extrabold hover:underline">{hit.name}</p>
                    <p className="muted truncate text-sm">{hit.headline ?? '—'}</p>
                </button>
                <p className="muted text-sm font-semibold">{meta}</p>
            </div>
            {hit.skills.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                    {hit.skills.map((s) => <span key={s} className={chip} style={{ background: 'var(--surface-2)' }}>{s}</span>)}
                </div>
            )}
            {hit.reasons.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                    {hit.reasons.map((r) => <span key={r} className={`${chip} bg-amber-500/15 text-amber-700 dark:text-amber-300`}>{r}</span>)}
                </div>
            )}
            {children}
        </div>
    )
}

function StatusIcon({ status }: { status: CriterionResult['status'] }) {
    if (status === 'met') return <CheckCircle2 size={17} className="mt-0.5 shrink-0 text-emerald-500" aria-label="Rempli" />
    if (status === 'to_confirm') return <CircleHelp size={17} className="mt-0.5 shrink-0 text-amber-500" aria-label="À confirmer" />
    return <XCircle size={17} className="mt-0.5 shrink-0 text-red-500" aria-label="Manquant" />
}

function CandidateDrawer({ id, anonymous, onClose }: { id: number; anonymous: boolean; onClose: () => void }) {
    const toast = useToast()
    const [c, setC] = useState<CandidateDetail | null>(null)
    const [downloading, setDownloading] = useState<'plain' | 'anon' | null>(null)

    useEffect(() => {
        let cancelled = false
        fetchCandidate(id, anonymous).then((d) => { if (!cancelled) setC(d) }).catch((e) => { toast.error(getErrorMessage(e)); onClose() })
        return () => { cancelled = true }
    }, [id, anonymous]) // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        const onKey = (e: globalThis.KeyboardEvent) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', onKey)
        return () => window.removeEventListener('keydown', onKey)
    }, [onClose])

    async function download(anon: boolean) {
        setDownloading(anon ? 'anon' : 'plain')
        try { await downloadCandidate(id, anon) } catch (e) { toast.error(getErrorMessage(e)) } finally { setDownloading(null) }
    }

    const d = c?.data
    return (
        <div className="fixed inset-0 z-50">
            <div className="absolute inset-0 bg-black/40" onClick={onClose} />
            <aside role="dialog" aria-modal="true" aria-label="Fiche candidat" className="card absolute inset-y-0 right-0 w-full max-w-xl overflow-y-auto rounded-none border-y-0 border-r-0 p-6 shadow-2xl">
                {!c || !d ? (
                    <div className="grid h-64 place-items-center"><LoaderCircle className="text-brand-500 animate-spin" size={26} /></div>
                ) : (
                    <div className="space-y-6">
                        <div className="flex items-start justify-between gap-4">
                            <div className="min-w-0">
                                <h2 className="break-words text-2xl font-extrabold">{c.name}</h2>
                                <p className="muted">{d.headline ?? '—'}</p>
                                <p className="muted mt-1 text-sm font-semibold">
                                    {[d.location, `${c.years} ans d'expérience`, c.job_family && JOB_FAMILIES[c.job_family]].filter(Boolean).join(' · ')}
                                </p>
                            </div>
                            <button onClick={onClose} className="btn-icon shrink-0" aria-label="Fermer"><X size={18} /></button>
                        </div>

                        {anonymous && <Notice>Version anonymisée : identité, contacts et liens masqués. Relis-la avant de l'envoyer.</Notice>}
                        {!anonymous && (d.email || d.phone) && <p className="text-sm">{[d.email, d.phone].filter(Boolean).join(' · ')}</p>}
                        {d.summary && <p className="text-sm leading-relaxed">{d.summary}</p>}

                        {c.skills.length > 0 && (
                            <section>
                                <h3 className="mb-2 font-bold">Compétences</h3>
                                <div className="flex flex-wrap gap-1.5">{c.skills.map((s) => <span key={s} className={chip} style={{ background: 'var(--surface-2)' }}>{s}</span>)}</div>
                            </section>
                        )}
                        {c.inferred_skills.length > 0 && (
                            <section>
                                <h3 className="mb-1 font-bold">Compétences déduites par l'IA <span className="muted text-sm font-semibold">(à confirmer)</span></h3>
                                <ul className="space-y-1.5 text-sm">
                                    {c.inferred_skills.map((s) => (
                                        <li key={s.name}><span className={`${chip} bg-amber-500/15 text-amber-700 dark:text-amber-300`}>{s.name}</span> <span className="muted">{s.evidence}</span></li>
                                    ))}
                                </ul>
                            </section>
                        )}
                        {(d.experiences?.length ?? 0) > 0 && (
                            <section>
                                <h3 className="mb-2 font-bold">Expériences</h3>
                                <ul className="space-y-3 text-sm">
                                    {d.experiences!.map((e, i) => (
                                        <li key={i}>
                                            <p className="font-semibold">{[e.title, e.company].filter(Boolean).join(' — ')}</p>
                                            <p className="muted text-xs">{[e.start_date, e.is_current ? "aujourd'hui" : e.end_date].filter(Boolean).join(' → ')}</p>
                                            {e.description && <p className="mt-1 whitespace-pre-line">{e.description}</p>}
                                        </li>
                                    ))}
                                </ul>
                            </section>
                        )}
                        {(d.education?.length ?? 0) > 0 && (
                            <section>
                                <h3 className="mb-2 font-bold">Formations</h3>
                                <ul className="space-y-1 text-sm">
                                    {d.education!.map((e, i) => <li key={i}>{[e.degree, e.field, e.institution, e.year].filter(Boolean).join(', ')}</li>)}
                                </ul>
                            </section>
                        )}
                        {(d.languages?.length ?? 0) > 0 && (
                            <p className="text-sm"><span className="font-bold">Langues : </span>{d.languages!.map((l) => l.language + (l.level ? ` (${l.level})` : '')).join(' · ')}</p>
                        )}

                        <div className="grid gap-3 sm:grid-cols-2">
                            <button onClick={() => void download(false)} disabled={downloading !== null} className="btn-primary">
                                {downloading === 'plain' ? <LoaderCircle size={16} className="animate-spin" /> : <Download size={16} />} Dossier (DOCX)
                            </button>
                            <button onClick={() => void download(true)} disabled={downloading !== null} className="btn-ghost">
                                {downloading === 'anon' ? <LoaderCircle size={16} className="animate-spin" /> : <EyeOff size={16} />} Version anonymisée
                            </button>
                        </div>
                        <Link to={`/app/documents/${c.document_id}`} className="text-brand-500 inline-flex items-center gap-1.5 text-sm font-semibold">
                            <FileSearch size={16} /> Ouvrir la relecture du CV
                        </Link>
                    </div>
                )}
            </aside>
        </div>
    )
}

function SearchPanel({ anonymous, onOpen }: { anonymous: boolean; onOpen: (id: number) => void }) {
    const [q, setQ] = useState('')
    const [minYears, setMinYears] = useState('')
    const [skills, setSkills] = useState<string[]>([])
    const [language, setLanguage] = useState('')
    const [location, setLocation] = useState('')
    const dq = useDebounce(q.trim(), 350)
    const dl = useDebounce(location.trim(), 350)
    const [res, setRes] = useState<SearchResponse | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const reqId = useRef(0)
    const toast = useToast()

    async function run() {
        const id = ++reqId.current
        setLoading(true)
        try {
            const r = await searchCandidates({ q: dq, minYears, skills, language: language.trim(), location: dl, anonymous })
            if (id === reqId.current) { setRes(r); setError('') }
        } catch (e) {
            if (id === reqId.current) setError(getErrorMessage(e))
        } finally {
            if (id === reqId.current) setLoading(false)
        }
    }
    useEffect(() => { void run() }, [dq, minYears, skills, language, dl, anonymous]) // eslint-disable-line react-hooks/exhaustive-deps

    async function reindex() {
        try {
            const { queued } = await reindexCandidates()
            toast.info(`Indexation lancée pour ${queued} CV. Actualise dans une minute.`)
        } catch (e) { toast.error(getErrorMessage(e)) }
    }

    return (
        <div className="space-y-5">
            <div className="card space-y-4 p-5">
                <div className="relative">
                    <Search size={18} className="muted absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input value={q} onChange={(e) => setQ(e.target.value)} className="input pl-11" maxLength={300}
                        placeholder="Ex. : data analyst Python santé, comptable fournisseurs…" aria-label="Rechercher un candidat" />
                </div>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <ChipInput label="Compétences requises" values={skills} onChange={setSkills} placeholder="Python, SQL…" />
                    <div>
                        <label htmlFor="min-years" className="mb-1.5 block text-sm font-semibold">Expérience minimale (ans)</label>
                        <input id="min-years" type="number" min={0} step="any" value={minYears} onChange={(e) => setMinYears(e.target.value)} className="input" />
                    </div>
                    <div>
                        <label htmlFor="lang" className="mb-1.5 block text-sm font-semibold">Langue</label>
                        <input id="lang" value={language} onChange={(e) => setLanguage(e.target.value)} className="input" placeholder="Anglais" />
                    </div>
                    <div>
                        <label htmlFor="loc" className="mb-1.5 block text-sm font-semibold">Localisation</label>
                        <input id="loc" value={location} onChange={(e) => setLocation(e.target.value)} className="input" placeholder="Lyon" />
                    </div>
                </div>
            </div>

            {res && res.unindexed > 0 && (
                <Notice>
                    {res.unindexed} CV ne sont pas encore indexés pour la recherche.{' '}
                    <button onClick={() => void reindex()} className="font-bold underline">Les indexer</button>
                </Notice>
            )}
            {error && <div role="alert" className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">{error}</div>}

            <div className="flex items-center justify-between">
                <p className="muted text-sm font-semibold">
                    {loading && !res ? 'Recherche…' : `${res?.items.length ?? 0} candidat${(res?.items.length ?? 0) > 1 ? 's' : ''}`}
                    {res && q.trim() && (res.semantic ? ' · recherche sémantique active' : ' · recherche par mots-clés uniquement')}
                </p>
                <button onClick={() => void run()} className="btn-icon" aria-label="Actualiser"><RefreshCw size={16} className={loading ? 'animate-spin' : ''} /></button>
            </div>

            <div className="space-y-4">
                {res?.items.map((h) => <CandidateCard key={h.document_id} hit={h} onOpen={() => onOpen(h.document_id)} />)}
                {res && res.items.length === 0 && !loading && (
                    <div className="card p-10 text-center"><p className="font-bold">Aucun candidat</p><p className="muted mt-1 text-sm">Ajoute et fais valider des CV, ou assouplis les filtres.</p></div>
                )}
            </div>
        </div>
    )
}

function MatchPanel({ anonymous, onOpen }: { anonymous: boolean; onOpen: (id: number) => void }) {
    const toast = useToast()
    const [text, setText] = useState('')
    const [criteria, setCriteria] = useState<JobCriteria | null>(null)
    const [results, setResults] = useState<MatchHit[] | null>(null)
    const [busy, setBusy] = useState<'parse' | 'match' | null>(null)

    async function analyze() {
        setBusy('parse'); setResults(null)
        try { setCriteria(await parseJob(text)) } catch (e) { toast.error(getErrorMessage(e)) } finally { setBusy(null) }
    }
    async function rank() {
        if (!criteria) return
        setBusy('match')
        try { setResults(await matchCandidates(criteria, text, anonymous)) } catch (e) { toast.error(getErrorMessage(e)) } finally { setBusy(null) }
    }
    const set = (patch: Partial<JobCriteria>) => setCriteria((c) => (c ? { ...c, ...patch } : c))

    return (
        <div className="space-y-5">
            <div className="card space-y-3 p-5">
                <label htmlFor="job" className="block text-sm font-semibold">Offre d'emploi</label>
                <textarea id="job" rows={6} className="input" value={text} onChange={(e) => setText(e.target.value)} placeholder="Colle ici le texte de l'offre…" />
                <button onClick={() => void analyze()} disabled={text.trim().length < 20 || busy !== null} className="btn-primary disabled:opacity-60">
                    {busy === 'parse' ? <LoaderCircle size={16} className="animate-spin" /> : <Sparkles size={16} />} Analyser l'offre
                </button>
            </div>

            {criteria && (
                <div className="card space-y-4 p-5">
                    <div>
                        <h3 className="font-bold">Critères détectés</h3>
                        <p className="muted text-sm">Vérifie et corrige : les candidats sont évalués sur ces critères exacts.</p>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                        <div className="sm:col-span-2">
                            <label htmlFor="jt" className="mb-1.5 block text-sm font-semibold">Poste</label>
                            <input id="jt" className="input" value={criteria.title ?? ''} onChange={(e) => set({ title: e.target.value || null })} />
                        </div>
                        <ChipInput label="Indispensables" values={criteria.must_have} onChange={(v) => set({ must_have: v })} placeholder="Ajouter…" />
                        <ChipInput label="Souhaités" values={criteria.nice_to_have} onChange={(v) => set({ nice_to_have: v })} placeholder="Ajouter…" />
                        <div>
                            <label htmlFor="jy" className="mb-1.5 block text-sm font-semibold">Expérience minimale (ans)</label>
                            <input id="jy" type="number" min={0} step="any" className="input" value={criteria.min_years ?? ''} onChange={(e) => set({ min_years: e.target.value === '' ? null : Number(e.target.value) })} />
                        </div>
                        <ChipInput label="Langues exigées" values={criteria.languages} onChange={(v) => set({ languages: v })} placeholder="Anglais…" />
                    </div>
                    <button onClick={() => void rank()} disabled={busy !== null} className="btn-primary">
                        {busy === 'match' ? <LoaderCircle size={16} className="animate-spin" /> : <Search size={16} />} Classer les candidats
                    </button>
                </div>
            )}

            {results && (
                <div className="space-y-4">
                    <p className="muted text-xs">Classement : critères indispensables remplis, puis à confirmer, puis souhaités. À égalité, les profils sémantiquement proches de l'offre passent en premier. C'est une aide à la lecture : la décision reste humaine.</p>
                    {results.length === 0 && <div className="card p-10 text-center font-bold">Aucun CV indexé à évaluer</div>}
                    {results.map((h) => (
                        <CandidateCard key={h.document_id} hit={{ ...h, reasons: [] }} onOpen={() => onOpen(h.document_id)}>
                            <p className="mt-3 text-sm font-bold">
                                Indispensables : {h.summary.must_met}/{h.summary.must_total}
                                {h.summary.must_to_confirm > 0 && ` (+${h.summary.must_to_confirm} à confirmer)`}
                                {h.summary.nice_total > 0 && ` · Souhaités : ${h.summary.nice_met}/${h.summary.nice_total}`}
                            </p>
                            <ul className="mt-2 space-y-1.5 text-sm">
                                {h.criteria.map((c, i) => (
                                    <li key={i} className="flex gap-2">
                                        <StatusIcon status={c.status} />
                                        <span><span className="font-semibold">{c.label}</span>{c.kind === 'nice' && <span className="muted"> (souhaité)</span>} <span className="muted">· {c.evidence}</span></span>
                                    </li>
                                ))}
                            </ul>
                        </CandidateCard>
                    ))}
                </div>
            )}
        </div>
    )
}

export default function Candidates() {
    usePageTitle('Candidats')
    const [tab, setTab] = useState<'search' | 'match'>('search')
    const [anonymous, setAnonymous] = useState(false)
    const [openId, setOpenId] = useState<number | null>(null)

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Candidats</h1>
                    <p className="muted mt-1">Recherche dans le vivier et comparaison à une offre.</p>
                </div>
                <button onClick={() => setAnonymous(!anonymous)} aria-pressed={anonymous} className={`btn-ghost ${anonymous ? 'border-brand-500 ring-2 ring-brand-500/30' : ''}`}>
                    <EyeOff size={16} /> Mode anonymisé {anonymous ? ': activé' : ''}
                </button>
            </div>

            <div role="group" aria-label="Mode" className="flex w-fit gap-1 rounded-xl p-1" style={{ background: 'var(--surface-2)' }}>
                {([['search', 'Recherche'], ['match', "Matching avec une offre"]] as const).map(([id, label]) => (
                    <button key={id} onClick={() => setTab(id)} aria-pressed={tab === id}
                        className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${tab === id ? 'bg-[var(--surface)] shadow-sm' : 'muted hover:text-[var(--text)]'}`}>
                        {label}
                    </button>
                ))}
            </div>

            {tab === 'search' ? <SearchPanel anonymous={anonymous} onOpen={setOpenId} /> : <MatchPanel anonymous={anonymous} onOpen={setOpenId} />}
            {openId !== null && <CandidateDrawer id={openId} anonymous={anonymous} onClose={() => setOpenId(null)} />}
        </div>
    )
}