import { createFileRoute } from '@tanstack/react-router'
import { BatchUpload } from '@/features/batch'

export const Route = createFileRoute('/_authenticated/batch/')({
  component: BatchUpload,
})
