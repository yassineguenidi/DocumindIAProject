import { Link } from 'react-router-dom'
import { LegalLayout, LegalSection, Ph } from '../components/legal/LegalLayout'

import { usePageTitle } from '../hooks/usePageTitle'


export default function LegalNotice() {
    usePageTitle('Mentions légales')
    return (
        <LegalLayout title="Mentions légales">
            <LegalSection title="Éditeur du site">
                <p>
                    Le site DocuMind AI est édité par <Ph>raison sociale, ou nom de l'entrepreneur individuel</Ph>,{' '}
                    <Ph>forme juridique</Ph>, immatriculée sous le numéro <Ph>SIREN / RCS</Ph>, dont le siège est situé{' '}
                    <Ph>adresse complète</Ph>.
                </p>
                <p>Contact : <Ph>adresse email</Ph>. Directeur de la publication : <Ph>nom</Ph>.</p>
            </LegalSection>

            <LegalSection title="Hébergement">
                <p>Le site et ses données sont hébergés par <Ph>nom de l'hébergeur</Ph>, <Ph>adresse de l'hébergeur</Ph>.</p>
            </LegalSection>

            <LegalSection title="Propriété intellectuelle">
                <p>
                    L'ensemble des éléments du site (textes, graphismes, logo, code) est protégé par le droit de la propriété
                    intellectuelle. Toute reproduction ou réutilisation sans autorisation écrite préalable est interdite.
                </p>
            </LegalSection>

            <LegalSection title="Responsabilité">
                <p>
                    L'éditeur s'efforce d'assurer l'exactitude des informations publiées, sans pouvoir garantir l'absence
                    d'erreur. Les données extraites automatiquement par l'IA doivent être vérifiées par l'utilisateur avant
                    toute utilisation ; l'éditeur ne saurait être tenu responsable d'une décision prise sur la seule base de
                    ces résultats.
                </p>
            </LegalSection>

            <LegalSection title="Données personnelles">
                <p>Le traitement de vos données personnelles est détaillé dans notre <Link to="/confidentialite">politique de confidentialité</Link>.</p>
            </LegalSection>
        </LegalLayout>
    )
}