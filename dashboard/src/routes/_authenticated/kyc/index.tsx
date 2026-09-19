import { createFileRoute } from '@tanstack/react-router'
import { KYCDashboard } from '@/features/kyc'

export const Route = createFileRoute('/_authenticated/kyc/')({
  component: KYCDashboard,
})
