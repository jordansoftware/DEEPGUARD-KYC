import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { Badge } from '@/components/ui/badge'

interface KycCase {
  id: string
  applicant: string
  doc_type: string
  status: string
  score: number
  submitted: string
}

const statusVariant: Record<string, 'default' | 'destructive' | 'secondary' | 'outline'> = {
  pending: 'secondary',
  review: 'outline',
  approved: 'default',
  rejected: 'destructive',
}

export function RecentCases() {
  const { data } = useQuery<{ cases: KycCase[] }>({
    queryKey: ['kyc-cases-recent'],
    queryFn: async () => {
      return apiFetch('/kyc/cases?page=1&page_size=5')
    },
  })

  if (!data?.cases?.length) {
    return (
      <div className='flex items-center justify-center h-40 text-muted-foreground text-sm'>
        No recent cases yet.
      </div>
    )
  }

  return (
    <div className='space-y-4'>
      {data.cases.map((c) => (
        <div key={c.id} className='flex items-center justify-between gap-3'>
          <div className='min-w-0 flex-1'>
            <p className='text-sm font-medium truncate'>{c.applicant}</p>
            <p className='text-xs text-muted-foreground'>
              {c.doc_type} · {new Date(c.submitted).toLocaleDateString()}
            </p>
          </div>
          <div className='flex items-center gap-2 shrink-0'>
            <span className='text-xs font-mono text-muted-foreground'>{c.score}</span>
            <Badge variant={statusVariant[c.status] ?? 'outline'}>
              {c.status}
            </Badge>
          </div>
        </div>
      ))}
    </div>
  )
}
