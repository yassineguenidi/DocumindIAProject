import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

export function ScrollToTop() {
    const { pathname, hash } = useLocation()
    useEffect(() => {
        if (!hash) { window.scrollTo(0, 0); return }
        document.getElementById(hash.slice(1))?.scrollIntoView()
    }, [pathname, hash])
    return null
}