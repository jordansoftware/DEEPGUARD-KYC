import { createFileRoute } from '@tanstack/react-router'
import { AnalysisResults } from '@/features/analysis'

export const Route = createFileRoute('/_authenticated/analysis/')({
  component: AnalysisResults,
})
