import { LegalLayout, LegalSection, Ph } from '../components/legal/LegalLayout'

import { usePageTitle } from '../hooks/usePageTitle'


export default function Privacy() {
    usePageTitle('Politique de confidentialité')
    return (
        <LegalLayout title="Politique de confidentialité">
            <LegalSection title="1. Responsable du traitement">
                <p>
                    Le responsable du traitement des données de compte est <Ph>raison sociale</Ph>, <Ph>adresse</Ph>.
                    Contact pour toute question : <Ph>adresse email</Ph>.
                </p>
            </LegalSection>

            <LegalSection title="2. Données collectées">
                <ul>
                    <li><strong>Compte :</strong> nom, prénom, adresse email, nom de l'entreprise. Le mot de passe est conservé uniquement sous forme hachée.</li>
                    <li><strong>Documents :</strong> les fichiers que vous déposez et les données qui en sont extraites.</li>
                    <li><strong>Données techniques :</strong> journaux de connexion (adresse IP, date) à des fins de sécurité. <Ph>à confirmer selon votre hébergement</Ph></li>
                </ul>
            </LegalSection>

            <LegalSection title="3. Finalités et bases légales">
                <ul>
                    <li>Fournir le service et gérer votre compte : exécution du contrat.</li>
                    <li>Assurer la sécurité du service et prévenir les abus : intérêt légitime.</li>
                    <li>Respecter nos obligations légales, comptables et fiscales : obligation légale.</li>
                </ul>
            </LegalSection>

            <LegalSection title="4. Vos documents">
                <p>
                    Pour les documents que vous nous confiez, vous restez responsable du traitement et nous agissons comme
                    sous-traitant, uniquement pour fournir le service. Un accord de sous-traitance est disponible{' '}
                    <Ph>à confirmer : sur demande / dans les conditions générales</Ph>. Vous pouvez supprimer un document et son
                    fichier à tout moment depuis votre espace.
                </p>
            </LegalSection>

            <LegalSection title="5. Destinataires et sous-traitants">
                <ul>
                    <li>Hébergement : <Ph>nom, pays</Ph>.</li>
                    <li>Extraction par intelligence artificielle : <Ph>nom du fournisseur, pays, garanties appliquées</Ph>. Le contenu textuel des documents peut lui être transmis pour en extraire les informations.</li>
                    <li>Paiement : <Ph>à compléter lors de la mise en place du paiement</Ph>.</li>
                    <li>Connexion avec Google (facultative) : Google LLC. Nous recevons votre nom, votre adresse email et un identifiant Google ; aucun autre accès à votre compte Google.</li>
                </ul>
            </LegalSection>

            <LegalSection title="6. Durées de conservation">
                <p>
                    Les données de compte sont conservées pendant la durée de la relation contractuelle, puis{' '}
                    <Ph>durée à définir</Ph>. Les documents sont conservés jusqu'à leur suppression par vos soins ou la
                    clôture du compte, puis supprimés sous <Ph>délai à définir</Ph>.
                </p>
            </LegalSection>

            <LegalSection title="7. Transferts hors Union européenne">
                <p><Ph>Indiquez si des données sont transférées hors UE (notamment via le fournisseur d'IA) et les garanties appliquées, ou précisez qu'il n'y en a aucun.</Ph></p>
            </LegalSection>

            <LegalSection title="8. Vos droits">
                <p>
                    Vous disposez des droits d'accès, de rectification, d'effacement, de limitation, d'opposition et de
                    portabilité de vos données. Pour les exercer, écrivez à <Ph>adresse email</Ph>. Vous pouvez aussi
                    introduire une réclamation auprès de la CNIL (<a href="https://www.cnil.fr" target="_blank" rel="noreferrer">cnil.fr</a>).
                </p>
            </LegalSection>

            <LegalSection title="9. Sécurité">
                <p>
                    Les mots de passe sont hachés, l'accès au service est authentifié et chaque entreprise n'accède qu'à ses
                    propres documents.
                </p>
            </LegalSection>

            <LegalSection title="10. Cookies et stockage local">
                <p>
                    Le site n'utilise ni cookie publicitaire ni outil de suivi. Il enregistre dans votre navigateur un jeton de
                    session et votre préférence de thème, nécessaires à son fonctionnement.
                </p>
            </LegalSection>
        </LegalLayout>
    )
}