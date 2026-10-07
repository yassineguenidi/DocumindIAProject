export interface User {
    id: number
    first_name: string
    last_name: string
    email: string
    role: string
    company_id: number
    company_name: string
    plan: string
    has_password: boolean
}

export interface RegisterPayload {
    first_name: string
    last_name: string
    email: string
    password: string
    company_name: string
}

export type StatusFilter = 'all' | 'in_progress' | 'done' | 'failed'

export type DocStatus = 'uploading' | 'queued' | 'ocr' | 'extraction' | 'validation' | 'done' | 'failed'

export interface DocumentItem {
    id: number
    original_filename: string
    mime_type: string
    size_bytes: number
    status: DocStatus
    doc_type: string | null
    extracted_data: unknown
    error_message: string | null
    created_at: string
}

export interface DocumentList { items: DocumentItem[]; total: number }

export interface Usage {
    plan: string
    quota: number | null
    used: number
    remaining: number | null
    period_start: string
    max_file_size_mb: number
}

export interface Stats {
    total: number
    in_progress: number
    done: number
    failed: number
    activity: { date: string; count: number }[]
}


export interface Plan {
    code: string
    name: string
    monthly_doc_quota: number | null
    max_file_size_mb: number
}


export interface LayoutWord { t: string; x: number; y: number; w: number; h: number }
export interface LayoutPage { number: number; width: number; height: number; words: LayoutWord[] }
export interface Layout { kind: 'pdf' | 'image'; pages: LayoutPage[] }

export interface ValidationIssue {
    code: string
    severity: 'error' | 'warning'
    message: string
    field: string | null
    ref_document_id?: number
}

export interface Review {
    validated: boolean
    validated_with_issues?: boolean
    by: number
    at: string
    corrected_fields: string[]
}

export interface CandidateHit {
  document_id: number
  name: string
  headline: string | null
  location: string | null
  years: number
  job_family: string | null
  skills: string[]
  languages: string[]
  reasons: string[]
}
export interface SearchResponse { items: CandidateHit[]; unindexed: number; semantic: boolean }
export interface JobCriteria {
  title: string | null
  must_have: string[]
  nice_to_have: string[]
  min_years: number | null
  languages: string[]
}
export interface CriterionResult {
  kind: 'must' | 'nice' | 'years' | 'language'
  label: string
  status: 'met' | 'to_confirm' | 'missing'
  evidence: string
}
export interface MatchHit extends CandidateHit {
  criteria: CriterionResult[]
  summary: { must_met: number; must_to_confirm: number; must_total: number; nice_met: number; nice_total: number }
}
export interface CvView {
  first_name?: string | null
  last_name?: string | null
  headline?: string | null
  summary?: string | null
  location?: string | null
  email?: string | null
  phone?: string | null
  experiences?: { title?: string | null; company?: string | null; start_date?: string | null; end_date?: string | null; is_current?: boolean; description?: string | null }[]
  education?: { degree?: string | null; field?: string | null; institution?: string | null; year?: number | null }[]
  languages?: { language: string; level?: string | null }[]
  certifications?: { name: string; issuer?: string | null; year?: number | null }[]
}
export interface CandidateDetail {
  document_id: number
  name: string
  filename: string | null
  years: number
  job_family: string | null
  data: CvView
  skills: string[]
  inferred_skills: { name: string; evidence: string }[]
}
export interface Supplier {
  key: string
  name: string
  siret: string | null
  vat_number: string | null
  invoice_count: number
  totals: { currency: string; total: number }[]
  last_date: string | null
  ibans: { iban: string; count: number }[]
  invoices: { document_id: number; number: string | null; date: string | null; total_ttc: number | null; currency: string | null; filename: string }[]
}