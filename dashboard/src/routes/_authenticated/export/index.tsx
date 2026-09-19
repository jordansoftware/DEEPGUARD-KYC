import { createFileRoute } from '@tanstack/react-router'
import { ExportPage } from '@/features/export'

export const Route = createFileRoute('/_authenticated/export/')({
  component: ExportPage,
})
