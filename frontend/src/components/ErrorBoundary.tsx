import { Component, type ErrorInfo, type ReactNode } from 'react'

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
    state = { failed: false }

    static getDerivedStateFromError() { return { failed: true } }

    componentDidCatch(error: Error, info: ErrorInfo) {
        console.error(error, info.componentStack)
    }

    render() {
        if (!this.state.failed) return this.props.children
        return (
            <div className="bg-mesh grid min-h-screen place-items-center p-6">
                <div className="card glass shadow-soft max-w-md space-y-4 p-10 text-center">
                    <h1 className="text-2xl font-extrabold">Une erreur est survenue</h1>
                    <p className="muted">Quelque chose s'est mal passé. Rechargez la page ou revenez à l'accueil.</p>
                    <div className="flex justify-center gap-3">
                        <button onClick={() => window.location.reload()} className="btn-ghost">Recharger</button>
                        <button onClick={() => window.location.assign('/')} className="btn-primary">Accueil</button>
                    </div>
                </div>
            </div>
        )
    }
}