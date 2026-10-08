import { clearCookies } from '@/test-utils/cookies'
import { beforeEach, describe, expect, it, vi } from 'vitest'

async function importAuthStore() {
  const { useAuthStore } = await import('./auth-store')
  return useAuthStore
}

describe('useAuthStore', () => {
  beforeEach(() => {
    clearCookies()
    vi.resetModules()
  })

  it('starts with an empty API key when nothing is persisted', async () => {
    const useAuthStore = await importAuthStore()
    expect(useAuthStore.getState().apiKey).toBe('')
  })

  it('persists the API key so a new store instance reads it back', async () => {
    const useAuthStore = await importAuthStore()
    useAuthStore.getState().setApiKey('dg_test_key')

    vi.resetModules()
    const reloaded = await importAuthStore()
    expect(reloaded.getState().apiKey).toBe('dg_test_key')
  })

  it('resetApiKey clears the key and drops persistence', async () => {
    const useAuthStore = await importAuthStore()
    useAuthStore.getState().setApiKey('dg_test_key')
    useAuthStore.getState().resetApiKey()
    expect(useAuthStore.getState().apiKey).toBe('')

    vi.resetModules()
    const reloaded = await importAuthStore()
    expect(reloaded.getState().apiKey).toBe('')
  })
})
