const API_BASE = '/api'

// Default key used when no key is stored yet (bootstrapping).
// The backend seeds this key on startup.
const DEFAULT_KEY = 'dg_demo'

export async function apiFetch(path: string, options?: RequestInit) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> || {}),
  }

  // Add API key if available in localStorage, otherwise fall back to the default
  const apiKey = localStorage.getItem('deepguard_api_key') || DEFAULT_KEY
  if (!headers['X-API-Key']) {
    headers['X-API-Key'] = apiKey
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || `API error ${res.status}`)
  }
  return res.json()
}
