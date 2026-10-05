import { api } from './api'
import type { Plan, Usage } from '../types'

export const fetchPlans = () => api.get<Plan[]>('/billing/plans').then((r) => r.data)
export const changePlan = (planCode: string) =>
  api.post<Usage>('/billing/change-plan', { plan_code: planCode }).then((r) => r.data)
export const cancelPlan = () => api.post<Usage>('/billing/cancel').then((r) => r.data)