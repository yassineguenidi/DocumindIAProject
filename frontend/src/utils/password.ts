export const passwordRules = [
    { id: 'len', label: '10 caractères minimum', test: (p: string) => p.length >= 10 },
    { id: 'upper', label: 'Une majuscule', test: (p: string) => /[A-Z]/.test(p) },
    { id: 'lower', label: 'Une minuscule', test: (p: string) => /[a-z]/.test(p) },
    { id: 'digit', label: 'Un chiffre', test: (p: string) => /\d/.test(p) },
]

export function passwordStrength(p: string): { score: number; label: string } {
    const passed = passwordRules.filter((r) => r.test(p)).length
    const bonus = passed === 4 && (p.length >= 14 || /[^A-Za-z0-9]/.test(p))
    const score = p.length === 0 ? 0 : bonus ? 4 : passed === 4 ? 3 : passed >= 2 ? 2 : 1
    return { score, label: ['', 'Faible', 'Moyen', 'Bon', 'Excellent'][score] }
}