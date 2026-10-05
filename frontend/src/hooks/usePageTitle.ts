import { useEffect } from 'react'

const BASE = 'DocuMind AI'

export function usePageTitle(title?: string) {
    useEffect(() => {
        document.title = title ? `${title} · ${BASE}` : `${BASE} : automatisation documentaire par IA`
    }, [title])
}