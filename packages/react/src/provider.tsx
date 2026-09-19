'use client'

import React, { createContext, useContext } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { DeepGuardConfig } from './types'

const DeepGuardContext = createContext<DeepGuardConfig>({ apiUrl: '/api' })

export function useDeepGuard() {
  return useContext(DeepGuardContext)
}

const queryClient = new QueryClient()

export function DeepGuardProvider({
  config,
  children,
}: {
  config: DeepGuardConfig
  children: React.ReactNode
}) {
  return (
    <DeepGuardContext.Provider value={config}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </DeepGuardContext.Provider>
  )
}
