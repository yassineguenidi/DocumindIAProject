const KEY = 'documind_token'

export const tokenStorage = {
  get(): string | null {
    try { return localStorage.getItem(KEY) } catch { return null }
  },
  set(token: string) {
    try { localStorage.setItem(KEY, token) } catch { /* stockage indisponible */ }
  },
  clear() {
    try { localStorage.removeItem(KEY) } catch { /* stockage indisponible */ }
  },
}