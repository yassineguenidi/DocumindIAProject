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

