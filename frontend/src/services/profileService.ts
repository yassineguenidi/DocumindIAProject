import { api } from './api'
import type { User } from '../types'

export const updateProfile = (p: { first_name: string; last_name: string; company_name?: string }) =>
    api.patch<User>('/auth/me', p).then((r) => r.data)

export const changePassword = (currentPassword: string, newPassword: string) =>
    api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword })