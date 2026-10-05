export const CONTACT_EMAIL = 'contact@exemple.fr' // À REMPLACER par votre vraie adresse

export interface PlanInfo {
  code: 'free' | 'starter' | 'business' | 'enterprise'
  name: string
  price: string
  monthly: boolean
  quota: string
  size: string
  features: string[]
  popular?: boolean
}

// PRIX D'EXEMPLE : à remplacer par vos vrais tarifs.
// Les quotas et tailles affichés ici pour la page d'accueil doivent rester alignés avec seed_plans.py.
export const PLAN_CATALOG: PlanInfo[] = [
  { code: 'free', name: 'Free', price: 'Gratuit', monthly: false, quota: '10 documents / mois', size: '5 Mo par fichier', features: ['Classification et extraction', 'Export JSON'] },
  { code: 'starter', name: 'Starter', price: '29 €', monthly: true, quota: '100 documents / mois', size: '10 Mo par fichier', features: ['Classification et extraction', 'Exports JSON et Excel'] },
  { code: 'business', name: 'Business', price: '99 €', monthly: true, quota: '1 000 documents / mois', size: '25 Mo par fichier', features: ['Classification et extraction', 'Exports JSON et Excel', 'Validation avancée'], popular: true },
  { code: 'enterprise', name: 'Enterprise', price: 'Sur devis', monthly: false, quota: 'Documents illimités', size: '50 Mo par fichier', features: ['Intégrations ERP / CRM', 'On-premise (bientôt)', 'Accompagnement dédié'] },
]