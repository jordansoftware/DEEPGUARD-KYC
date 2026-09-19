import { createFileRoute } from '@tanstack/react-router'
import { HistoryPage } from '@/features/history'

export const Route = createFileRoute('/_authenticated/history/')({
  component: HistoryPage,
})
