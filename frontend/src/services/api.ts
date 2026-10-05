import axios from 'axios'
import { tokenStorage } from './tokenStorage'

export const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1',
})

api.interceptors.request.use((config) => {
    const token = tokenStorage.get()
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// Session expirée : on nettoie et on prévient l'AuthContext
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && tokenStorage.get()) {
            tokenStorage.clear()
            window.dispatchEvent(new Event('auth:expired'))
        }
        return Promise.reject(error)
    },
)