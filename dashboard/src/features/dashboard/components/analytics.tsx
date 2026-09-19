import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { NumberTicker } from '@/components/ui/number-ticker'

interface OverviewData {
  total_cases: number
  by_status: Record<string, number>
  average_score: number
  verdicts: Record<string, number>
  approval_rate: number
}

interface SlaData {
  on_track: number
  overdue: number
  compliance_rate: number
}

export function Analytics() {
  const { data: overview } = useQuery<OverviewData>({
    queryKey: ['analytics-overview'],
    queryFn: async () => {
      return apiFetch('/analytics/overview')
    },
  })

  const { data: sla } = useQuery<SlaData>({
    queryKey: ['analytics-sla'],
    queryFn: async () => {
      return apiFetch('/analytics/sla-compliance')
    },
  })

  const { data: risk } = useQuery<{ distribution: Record<string, number>; total: number }>({
    queryKey: ['analytics-risk'],
    queryFn: async () => {
      return apiFetch('/analytics/risk-distribution')
    },
  })

  return (
    <div className='space-y-6'>
      <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Total Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              <NumberTicker value={overview?.total_cases ?? 0} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Avg Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              <NumberTicker value={overview?.average_score ?? 0} decimalPlaces={1} />
            </div>
            <p className='text-xs text-muted-foreground'>out of 100</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Approval Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold text-green-600'>
              <NumberTicker value={overview?.approval_rate ?? 0} decimalPlaces={1} />%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>SLA Compliance</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className='text-2xl font-bold'
              style={{ color: (sla?.compliance_rate ?? 0) >= 90 ? '#22c55e' : '#eab308' }}
            >
              <NumberTicker value={sla?.compliance_rate ?? 0} decimalPlaces={1} />%
            </div>
            <p className='text-xs text-muted-foreground'>
              {sla?.on_track ?? 0} on track, {sla?.overdue ?? 0} overdue
            </p>
          </CardContent>
        </Card>
      </div>

      <div className='grid gap-6 md:grid-cols-2'>
        <Card>
          <CardHeader>
            <CardTitle>Status Distribution</CardTitle>
            <CardDescription>Cases by current status</CardDescription>
          </CardHeader>
          <CardContent className='space-y-3'>
            {overview &&
              Object.entries(overview.by_status).map(([status, count]) => (
                <div key={status} className='flex items-center justify-between'>
                  <span className='text-sm capitalize'>{status}</span>
                  <div className='flex items-center gap-2'>
                    <div className='h-2 w-24 rounded-full bg-muted overflow-hidden'>
                      <div
                        className='h-full bg-primary'
                        style={{ width: `${(count / Math.max(overview.total_cases, 1)) * 100}%` }}
                      />
                    </div>
                    <span className='text-sm font-medium w-8 text-right'>{count}</span>
                  </div>
                </div>
              ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Distribution</CardTitle>
            <CardDescription>Score distribution across all cases</CardDescription>
          </CardHeader>
          <CardContent className='space-y-3'>
            {risk &&
              Object.entries(risk.distribution).map(([range, count]) => (
                <div key={range} className='flex items-center justify-between'>
                  <span className='text-sm'>{range}</span>
                  <div className='flex items-center gap-2'>
                    <div className='h-2 w-24 rounded-full bg-muted overflow-hidden'>
                      <div
                        className='h-full bg-primary'
                        style={{ width: `${(count / Math.max(risk.total, 1)) * 100}%` }}
                      />
                    </div>
                    <span className='text-sm font-medium w-8 text-right'>{count}</span>
                  </div>
                </div>
              ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>SLA Status</CardTitle>
            <CardDescription>Processing deadline compliance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className='grid grid-cols-2 gap-4'>
              <div className='text-center'>
                <div className='text-3xl font-bold text-green-500'>
                  <NumberTicker value={sla?.on_track ?? 0} />
                </div>
                <p className='text-sm text-muted-foreground'>On Track</p>
              </div>
              <div className='text-center'>
                <div className='text-3xl font-bold text-red-500'>
                  <NumberTicker value={sla?.overdue ?? 0} />
                </div>
                <p className='text-sm text-muted-foreground'>Overdue</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Verdicts</CardTitle>
            <CardDescription>Decision breakdown</CardDescription>
          </CardHeader>
          <CardContent className='space-y-3'>
            {overview &&
              Object.entries(overview.verdicts).map(([verdict, count]) => (
                <div key={verdict} className='flex items-center justify-between'>
                  <span className='text-sm capitalize'>{verdict}</span>
                  <span className='text-sm font-medium'>
                    <NumberTicker value={count} />
                  </span>
                </div>
              ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
