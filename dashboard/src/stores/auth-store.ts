import { create } from 'zustand'
import { getCookie, setCookie, removeCookie } from '@/lib/cookies'

const API_KEY_COOKIE = 'deepguard_api_key'

interface AuthState {
  apiKey: string
  setApiKey: (key: string) => void
  resetApiKey: () => void
}

export const useAuthStore = create<AuthState>()((set) => ({
  apiKey: getCookie(API_KEY_COOKIE) || '',
  setApiKey: (key: string) => {
    setCookie(API_KEY_COOKIE, key)
    set({ apiKey: key })
  },
  resetApiKey: () => {
    removeCookie(API_KEY_COOKIE)
    set({ apiKey: '' })
  },
}))
