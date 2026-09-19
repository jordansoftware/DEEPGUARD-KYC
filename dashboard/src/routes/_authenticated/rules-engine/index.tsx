import { createFileRoute } from '@tanstack/react-router'
import { RulesEngine } from '@/features/rules-engine'

export const Route = createFileRoute('/_authenticated/rules-engine/')({
  component: RulesEngine,
})
