import { api } from './api'
import type { RegisterPayload, User } from '../types'

export async function loginRequest(email: string, password: string): Promise<string> {
    // L'endpoint attend un formulaire OAuth2 : "username" contient l'email
    const body = new URLSearchParams({ username: email, password })
    const { data } = await api.post<{ access_token: string }>('/auth/login', body)
    return data.access_token
}

export async function registerRequest(payload: RegisterPayload): Promise<void> {
    await api.post('/auth/register', payload)
}

export async function fetchMe(): Promise<User> {
    const { data } = await api.get<User>('/auth/me')
    return data
}

export async function googleLoginRequest(credential: string): Promise<string> {
    const { data } = await api.post<{ access_token: string }>('/auth/google', { credential })
    return data.access_token
}