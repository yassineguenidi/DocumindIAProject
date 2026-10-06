import { Plus, Trash2, TriangleAlert } from 'lucide-react'
import type { FieldSpec, ListSpec, StringsSpec, TypeSpec } from '../../data/reviewSpecs'

export type Draft = Record<string, unknown>
type Row = Record<string, unknown>
type OnActive = (id: string, value: unknown) => void

function Control({ spec, id, value, onChange, onActive, warn }: {
    spec: FieldSpec; id: string; value: unknown; onChange: (v: unknown) => void; onActive: OnActive; warn: boolean
}) {
    const cls = `input ${warn ? 'border-amber-500' : ''}`
    const focus = () => onActive(id, value)
    const set = (v: unknown) => { onChange(v); onActive(id, v) }
    const text = (e: { target: { value: string } }) => set(spec.required ? e.target.value : e.target.value || null)

    switch (spec.kind) {
        case 'textarea':
            return <textarea id={id} aria-label={spec.label} rows={3} className={cls} value={(value as string) ?? ''} onFocus={focus} onChange={text} />
        case 'number':
        case 'int':
            return (
                <input
                    id={id} aria-label={spec.label} type="number" step={spec.kind === 'int' ? 1 : 'any'} className={cls}
                    placeholder={spec.placeholder} value={(value as number | null) ?? ''} onFocus={focus}
                    onChange={(e) => set(e.target.value === '' ? null : Number(e.target.value))}
                />
            )
        case 'date':
            return <input id={id} aria-label={spec.label} type="date" className={cls} value={(value as string) ?? ''} onFocus={focus} onChange={text} />
        case 'bool':
            return (
                <input
                    id={id} aria-label={spec.label} type="checkbox" className="h-5 w-5 accent-[var(--color-brand-500)]"
                    checked={Boolean(value)} onChange={(e) => onChange(e.target.checked)}
                />
            )
        case 'select':
            return (
                <select id={id} aria-label={spec.label} className={cls} value={(value as string) ?? ''} onChange={(e) => onChange(e.target.value)}>
                    {spec.options?.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
            )
        default:
            return (
                <input
                    id={id} aria-label={spec.label} type="text" className={cls} placeholder={spec.placeholder}
                    value={(value as string) ?? ''} onFocus={focus} onChange={text}
                />
            )
    }
}

function Field({ spec, id, value, onChange, onActive, issues }: {
    spec: FieldSpec; id: string; value: unknown; onChange: (v: unknown) => void; onActive: OnActive; issues?: string[]
}) {
    const warn = !!issues && issues.length > 0
    return (
        <div className={spec.wide ? 'sm:col-span-2' : ''}>
            <label htmlFor={id} className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold">
                {spec.label}
                {warn && <TriangleAlert size={14} className="text-amber-500" />}
            </label>
            <Control spec={spec} id={id} value={value} onChange={onChange} onActive={onActive} warn={warn} />
            {warn && <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">{issues!.join(' · ')}</p>}
        </div>
    )
}

function SectionTitle({ label, count, issues }: { label: string; count: number; issues?: string[] }) {
    return (
        <div className="mb-3">
            <h3 className="flex items-center gap-1.5 font-bold">
                {label} <span className="muted text-sm font-semibold">({count})</span>
                {issues && issues.length > 0 && <TriangleAlert size={15} className="text-amber-500" />}
            </h3>
            {issues && issues.length > 0 && <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">{issues.join(' · ')}</p>}
        </div>
    )
}

const addBtn = 'text-brand-500 inline-flex items-center gap-1 text-sm font-semibold'
const delBtn = 'muted rounded-lg p-2 transition hover:bg-red-500/10 hover:!text-red-500'

function ListEditor({ list, rows, onChange, onActive, issues }: {
    list: ListSpec; rows: Row[]; onChange: (rows: Row[]) => void; onActive: OnActive; issues?: string[]
}) {
    const update = (i: number, key: string, v: unknown) =>
        onChange(rows.map((r, idx) => (idx === i ? { ...r, [key]: v } : r)))
    const remove = (i: number) => onChange(rows.filter((_, idx) => idx !== i))

    return (
        <section>
            <SectionTitle label={list.label} count={rows.length} issues={issues} />
            <div className="space-y-3">
                {rows.map((row, i) =>
                    list.compact ? (
                        <div key={i} className="flex flex-wrap items-center gap-2">
                            {list.columns.map((c) => (
                                <div key={c.key} className="min-w-[8rem] flex-1">
                                    <Control
                                        spec={c} id={`${list.key}.${i}.${c.key}`} value={row[c.key]}
                                        onChange={(v) => update(i, c.key, v)} onActive={onActive} warn={false}
                                    />
                                </div>
                            ))}
                            <button type="button" onClick={() => remove(i)} className={delBtn} aria-label={`Supprimer ${list.item} ${i + 1}`}>
                                <Trash2 size={16} />
                            </button>
                        </div>
                    ) : (
                        <div key={i} className="rounded-xl border p-3" style={{ borderColor: 'var(--border)', background: 'var(--surface-2)' }}>
                            <div className="grid gap-3 sm:grid-cols-2">
                                {list.columns.map((c) => (
                                    <Field
                                        key={c.key} spec={c} id={`${list.key}.${i}.${c.key}`} value={row[c.key]}
                                        onChange={(v) => update(i, c.key, v)} onActive={onActive}
                                    />
                                ))}
                            </div>
                            <div className="mt-2 flex justify-end">
                                <button type="button" onClick={() => remove(i)} className={`${delBtn} inline-flex items-center gap-1 text-sm font-semibold`}>
                                    <Trash2 size={15} /> Supprimer {list.item} {i + 1}
                                </button>
                            </div>
                        </div>
                    ),
                )}
            </div>
            <button type="button" onClick={() => onChange([...rows, { ...list.empty }])} className={`${addBtn} mt-3`}>
                <Plus size={16} /> Ajouter {list.item}
            </button>
        </section>
    )
}

function StringsEditor({ spec, items, onChange }: { spec: StringsSpec; items: string[]; onChange: (items: string[]) => void }) {
    return (
        <section>
            <SectionTitle label={spec.label} count={items.length} />
            <div className="space-y-2">
                {items.map((item, i) => (
                    <div key={i} className="flex items-center gap-2">
                        <input
                            type="text" className="input" aria-label={`${spec.label} ${i + 1}`} value={item}
                            onChange={(e) => onChange(items.map((x, idx) => (idx === i ? e.target.value : x)))}
                        />
                        <button type="button" onClick={() => onChange(items.filter((_, idx) => idx !== i))} className={delBtn} aria-label={`Supprimer ${spec.label} ${i + 1}`}>
                            <Trash2 size={16} />
                        </button>
                    </div>
                ))}
            </div>
            <button type="button" onClick={() => onChange([...items, ''])} className={`${addBtn} mt-3`}>
                <Plus size={16} /> Ajouter
            </button>
        </section>
    )
}

export function ReviewForm({ spec, draft, onChange, onActive, issues }: {
    spec: TypeSpec
    draft: Draft
    onChange: (next: Draft) => void
    onActive: OnActive
    issues: Record<string, string[]>
}) {
    const set = (key: string, v: unknown) => onChange({ ...draft, [key]: v })
    return (
        <div className="space-y-8">
            <div className="grid gap-4 sm:grid-cols-2">
                {spec.scalars.map((f) => (
                    <Field
                        key={f.key} spec={f} id={`f-${f.key}`} value={draft[f.key]}
                        onChange={(v) => set(f.key, v)} onActive={onActive} issues={issues[f.key]}
                    />
                ))}
            </div>
            {spec.strings.map((s) => (
                <StringsEditor key={s.key} spec={s} items={(draft[s.key] as string[] | undefined) ?? []} onChange={(v) => set(s.key, v)} />
            ))}
            {spec.lists.map((l) => (
                <ListEditor
                    key={l.key} list={l} rows={(draft[l.key] as Row[] | undefined) ?? []}
                    onChange={(v) => set(l.key, v)} onActive={onActive} issues={issues[l.key]}
                />
            ))}
        </div>
    )
}