export type Kind = 'text' | 'textarea' | 'number' | 'int' | 'date' | 'bool' | 'select'

export interface FieldSpec {
    key: string
    label: string
    kind?: Kind
    options?: [string, string][]
    placeholder?: string
    wide?: boolean
    required?: boolean
}

export interface ListSpec {
    key: string
    label: string
    item: string
    columns: FieldSpec[]
    compact?: boolean
    empty: Record<string, unknown>
}

export interface StringsSpec { key: string; label: string }
export interface TypeSpec { scalars: FieldSpec[]; lists: ListSpec[]; strings: StringsSpec[] }

export const SPECS: Record<string, TypeSpec> = {
    invoice: {
        scalars: [
            { key: 'document_kind', label: 'Type', kind: 'select', options: [['invoice', 'Facture'], ['credit_note', 'Avoir']] },
            { key: 'language', label: 'Langue' },
            { key: 'supplier_name', label: 'Fournisseur' },
            { key: 'customer_name', label: 'Client' },
            { key: 'supplier_address', label: 'Adresse du fournisseur', kind: 'textarea', wide: true },
            { key: 'supplier_siret', label: 'SIRET' },
            { key: 'supplier_vat_number', label: 'N° de TVA' },
            { key: 'customer_siren', label: 'SIREN du client' },
            { key: 'invoice_number', label: 'N° de facture' },
            { key: 'invoice_date', label: 'Date de facture', kind: 'date' },
            { key: 'due_date', label: 'Échéance', kind: 'date' },
            { key: 'currency', label: 'Devise' },
            { key: 'total_ht', label: 'Total HT', kind: 'number' },
            { key: 'total_vat', label: 'TVA', kind: 'number' },
            { key: 'total_ttc', label: 'Total TTC', kind: 'number' },
            { key: 'iban', label: 'IBAN', wide: true },
        ],
        strings: [],
        lists: [
            {
                key: 'lines', label: 'Lignes', item: 'ligne',
                empty: { description: null, quantity: null, unit_price: null, vat_rate: null, total_ht: null },
                columns: [
                    { key: 'description', label: 'Désignation', wide: true },
                    { key: 'quantity', label: 'Quantité', kind: 'number' },
                    { key: 'unit_price', label: 'Prix unitaire HT', kind: 'number' },
                    { key: 'vat_rate', label: 'TVA (%)', kind: 'number' },
                    { key: 'total_ht', label: 'Total HT', kind: 'number' },
                ],
            },
            {
                key: 'vat_breakdown', label: 'TVA par taux', item: 'taux', compact: true,
                empty: { rate: null, base: null, amount: null },
                columns: [
                    { key: 'rate', label: 'Taux', kind: 'number', placeholder: 'Taux %' },
                    { key: 'base', label: 'Base HT', kind: 'number', placeholder: 'Base HT' },
                    { key: 'amount', label: 'Montant de TVA', kind: 'number', placeholder: 'TVA' },
                ],
            },
        ],
    },
    cv: {
        scalars: [
            { key: 'first_name', label: 'Prénom' },
            { key: 'last_name', label: 'Nom' },
            { key: 'headline', label: 'Titre professionnel', wide: true },
            { key: 'email', label: 'E-mail' },
            { key: 'phone', label: 'Téléphone' },
            { key: 'location', label: 'Localisation' },
            { key: 'language', label: 'Langue du CV' },
            { key: 'summary', label: 'Profil', kind: 'textarea', wide: true },
        ],
        strings: [{ key: 'links', label: 'Liens' }],
        lists: [
            {
                key: 'experiences', label: 'Expériences', item: 'expérience',
                empty: { title: null, company: null, location: null, start_date: null, end_date: null, is_current: false, description: null },
                columns: [
                    { key: 'title', label: 'Poste' },
                    { key: 'company', label: 'Employeur' },
                    { key: 'location', label: 'Lieu' },
                    { key: 'start_date', label: 'Début', placeholder: 'AAAA-MM' },
                    { key: 'end_date', label: 'Fin', placeholder: 'AAAA-MM' },
                    { key: 'is_current', label: 'Poste en cours', kind: 'bool' },
                    { key: 'description', label: 'Missions', kind: 'textarea', wide: true },
                ],
            },
            {
                key: 'education', label: 'Formations', item: 'formation',
                empty: { degree: null, field: null, institution: null, year: null },
                columns: [
                    { key: 'degree', label: 'Diplôme' },
                    { key: 'field', label: 'Spécialité' },
                    { key: 'institution', label: 'Établissement' },
                    { key: 'year', label: 'Année', kind: 'int' },
                ],
            },
            {
                key: 'skills', label: 'Compétences', item: 'compétence', compact: true,
                empty: { name: '', source: 'skills_section' },
                columns: [
                    { key: 'name', label: 'Compétence', placeholder: 'Compétence', required: true },
                    { key: 'source', label: 'Origine', kind: 'select', options: [['skills_section', 'Rubrique compétences'], ['experience', 'Expérience']] },
                ],
            },
            {
                key: 'languages', label: 'Langues parlées', item: 'langue', compact: true,
                empty: { language: '', level: null },
                columns: [
                    { key: 'language', label: 'Langue', placeholder: 'Langue', required: true },
                    { key: 'level', label: 'Niveau', placeholder: 'Niveau' },
                ],
            },
            {
                key: 'certifications', label: 'Certifications', item: 'certification', compact: true,
                empty: { name: '', issuer: null, year: null },
                columns: [
                    { key: 'name', label: 'Certification', placeholder: 'Certification', required: true },
                    { key: 'issuer', label: 'Organisme', placeholder: 'Organisme' },
                    { key: 'year', label: 'Année', kind: 'int', placeholder: 'Année' },
                ],
            },
        ],
    },
}

// Retire les lignes vides (obligatoires non renseignées) avant l'enregistrement
export function pruneDraft(spec: TypeSpec, draft: Record<string, unknown>): Record<string, unknown> {
    const out = { ...draft }
    for (const list of spec.lists) {
        const required = list.columns.filter((c) => c.required).map((c) => c.key)
        const rows = (out[list.key] as Record<string, unknown>[] | undefined) ?? []
        out[list.key] = rows.filter((r) => required.every((k) => String(r[k] ?? '').trim() !== ''))
    }
    for (const s of spec.strings) {
        const items = (out[s.key] as string[] | undefined) ?? []
        out[s.key] = items.map((x) => x.trim()).filter(Boolean)
    }
    return out
}