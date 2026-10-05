import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export function ActivityChart({ data }: { data: { date: string; count: number }[] }) {
    const fmt = new Intl.DateTimeFormat('fr-FR', { day: '2-digit', month: '2-digit' })
    const rows = data.map((d) => ({ ...d, label: fmt.format(new Date(`${d.date}T12:00:00`)) }))
    const tick = { fill: 'var(--muted)', fontSize: 12 }

    return (
        <div className="h-60" role="img" aria-label="Documents envoyés par jour sur les 14 derniers jours">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={rows} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                    <defs>
                        <linearGradient id="act-fill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#4f56ee" stopOpacity={0.45} />
                            <stop offset="100%" stopColor="#22b8e8" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                    <XAxis dataKey="label" tickLine={false} axisLine={false} tick={tick} interval="preserveStartEnd" />
                    <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={tick} />
                    <Tooltip
                        contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, color: 'var(--text)' }}
                        labelStyle={{ color: 'var(--muted)' }}
                    />
                    <Area type="monotone" name="Documents" dataKey="count" stroke="#4f56ee" strokeWidth={3} fill="url(#act-fill)" />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    )
}