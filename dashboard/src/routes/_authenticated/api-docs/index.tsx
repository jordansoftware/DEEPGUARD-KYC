import { createFileRoute } from '@tanstack/react-router'
import { APIDocsPage } from '@/features/api-docs'

export const Route = createFileRoute('/_authenticated/api-docs/')({
  component: APIDocsPage,
})
