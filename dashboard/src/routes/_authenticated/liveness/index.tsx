import { createFileRoute } from '@tanstack/react-router'
import { LivenessDetection } from '@/features/liveness'

export const Route = createFileRoute('/_authenticated/liveness/')({
  component: LivenessDetection,
})
