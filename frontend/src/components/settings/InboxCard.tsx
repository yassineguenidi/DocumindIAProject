import { useEffect, useState } from 'react'
import { Copy, LoaderCircle, RefreshCw } from 'lucide-react'
import { ConfirmDialog } from '../ui/ConfirmDialog'
import { Notice } from '../ui/Notice'
import { useToast } from '../../contexts/ToastContext'
import { fetchInbox, rotateInbox, saveInbox, type InboxInfo } from '../../services/exportService'
import { getErrorMessage } from '../../utils/errors'

export function InboxCard() {
    const toast = useToast()
    const [info, setInfo] = useState<InboxInfo | null>(null)
    const [allowed, setAllowed] = useState('')
    const [saving, setSaving] = useState(false)
    const [confirm, setConfirm] = useState(false)
    const [rotating, setRotating] = useState(false)

    useEffect(() => {
        fetchInbox().then((i) => { setInfo(i); setAllowed(i.allowed) }).catch((e) => toast.error(getErrorMessage(e)))
    }, []) // eslint-disable-line react-hooks/exhaustive-deps

    if (!info) return <div className="grid h-24 place-items-center"><LoaderCircle className="text-brand-500 animate-spin" size={22} /></div>
    if (!info.enabled) return <Notice>La réception par email n'est pas configurée sur ce serveur (variables IMAP_* du backend).</Notice>

    async function save() {
        setSaving(true)
        try { const i = await saveInbox(allowed); setInfo(i); setAllowed(i.allowed); toast.success('Expéditeurs autorisés enregistrés') } catch (e) { toast.error(getErrorMessage(e)) } finally { setSaving(false) }
    }
    async function rotate() {
        setRotating(true)
        try { setInfo(await rotateInbox()); toast.success('Nouvelle adresse générée') } catch (e) { toast.error(getErrorMessage(e)) } finally { setRotating(false); setConfirm(false) }
    }
    async function copy() {
        try { await navigator.clipboard.writeText(info!.address ?? ''); toast.success('Adresse copiée') } catch { toast.error('Copie impossible : sélectionne l\'adresse à la main') }
    }

    return (
        <div className="space-y-5">
            <p className="muted text-sm">Envoie tes documents en pièce jointe (PDF, PNG, JPG) à cette adresse : ils sont ajoutés et traités automatiquement, en quelques minutes.</p>
            <div className="flex flex-wrap items-center gap-2">
                <code className="min-w-0 flex-1 break-all rounded-xl px-3 py-2.5 text-sm font-semibold" style={{ background: 'var(--surface-2)' }}>{info.address}</code>
                <button onClick={() => void copy()} className="btn-icon" aria-label="Copier l'adresse"><Copy size={16} /></button>
                <button onClick={() => setConfirm(true)} className="btn-icon" aria-label="Générer une nouvelle adresse"><RefreshCw size={16} /></button>
            </div>
            <div>
                <label htmlFor="allowed" className="mb-1.5 block text-sm font-semibold">Expéditeurs autorisés en plus des membres de l'entreprise</label>
                <textarea id="allowed" rows={3} className="input" value={allowed} onChange={(e) => setAllowed(e.target.value)} placeholder={'compta@exemple.fr\n@cabinet-partenaire.fr'} />
                <p className="muted mt-1 text-xs">Une adresse ou un domaine (@exemple.fr) par ligne.{info.require_auth && ' Les mails dont l\'expéditeur n\'est pas authentifié sont refusés.'}</p>
            </div>
            <button onClick={() => void save()} disabled={saving || allowed === info.allowed} className="btn-primary disabled:opacity-60">
                {saving && <LoaderCircle size={16} className="animate-spin" />} Enregistrer
            </button>
            {confirm && (
                <ConfirmDialog
                    title="Générer une nouvelle adresse ?" tone="primary" confirmLabel="Générer" loading={rotating}
                    message="L'adresse actuelle cessera immédiatement de fonctionner. Pense à prévenir ceux qui l'utilisent."
                    onConfirm={() => void rotate()} onCancel={() => setConfirm(false)}
                />
            )}
        </div>
    )
}