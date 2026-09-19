import { createFileRoute } from '@tanstack/react-router'
import { RulesPage } from '@/features/rules'

export const Route = createFileRoute('/_authenticated/rules/')({
  component: RulesPage,
})
