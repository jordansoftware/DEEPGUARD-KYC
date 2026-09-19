import { useQuery } from '@tanstack/react-query'
import {
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle2,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { apiFetch } from '@/lib/api'

interface AnalyticsData {
  total_cases: number
  by_status: Record<string, number>
  average_score: number
  verdicts: Record<string, number>
  approval_rate: number
}

interface TrendData {
  date: string
  total: number
  approved: number
  rejected: number
  review: number
  avg_score: number
}

interface RiskDistribution {
  distribution: Record<string, number>
  total: number
}

interface SLACompliance {
  overdue: number
  on_track: number
  total_in_review: number
  compliance_rate: number
}

function StatCard({ title, value, icon: Icon, color, description }: {
  title: string
  value: number | string
  icon: React.ComponentType<{ className?: string }>
  color: string
  description?: string
}) {
  return (
    <Card>
      <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
        <CardTitle className='text-sm font-medium'>{title}</CardTitle>
        <Icon className={`h-4 w-4 ${color}`} />
      </CardHeader>
      <CardContent>
        <div className='text-2xl font-bold'>{value}</div>
        {description && <p className='text-xs text-muted-foreground'>{description}</p>}
      </CardContent>
    </Card>
  )
}

export function AnalyticsDashboard() {
  const { data: overview, isLoading, isError } = useQuery<AnalyticsData>({
    queryKey: ['analytics-overview'],
    queryFn: async () => {
      return apiFetch('/analytics/overview')
    },
  })

  const { data: trends } = useQuery<{ trends: TrendData[] }>({
    queryKey: ['analytics-trends'],
    queryFn: async () => {
      return apiFetch('/analytics/trends?days=30')
    },
  })

  const { data: risk } = useQuery<RiskDistribution>({
    queryKey: ['analytics-risk'],
    queryFn: async () => {
      return apiFetch('/analytics/risk-distribution')
    },
  })

  const { data: sla } = useQuery<SLACompliance>({
    queryKey: ['analytics-sla'],
    queryFn: async () => {
      return apiFetch('/analytics/sla-compliance')
    },
  })

  return (
    <>
      <Header>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ProfileDropdown />
      </Header>
      <Main>
        <div className='mb-6'>
          <h1 className='text-2xl font-bold tracking-tight'>Analytics</h1>
          <p className='text-muted-foreground'>
            Overview of KYC verification metrics and trends.
          </p>
        </div>

        {isLoading ? (
          <div className='flex h-64 items-center justify-center text-muted-foreground'>
            Loading analytics...
          </div>
        ) : isError ? (
          <div className='rounded-md border p-6 text-center text-sm text-muted-foreground'>
            Failed to load analytics. Please check your API key settings.
          </div>
        ) : (
          <>
        <div className='mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
          <StatCard title='Total Cases' value={overview?.total_cases ?? 0} icon={BarChart3} color='text-muted-foreground' />
          <StatCard title='Avg Score' value={`${overview?.average_score ?? 0}/100`} icon={TrendingUp} color='text-blue-500' />
          <StatCard title='Approval Rate' value={`${overview?.approval_rate ?? 0}%`} icon={CheckCircle2} color='text-green-500' />
          <StatCard title='SLA Compliance' value={`${sla?.compliance_rate ?? 0}%`} icon={Clock} color={sla?.compliance_rate ?? 100 >= 90 ? 'text-green-500' : 'text-yellow-500'} />
        </div>

        <div className='grid gap-6 md:grid-cols-2'>
          <Card>
            <CardHeader>
              <CardTitle>Status Distribution</CardTitle>
              <CardDescription>Cases by current status</CardDescription>
            </CardHeader>
            <CardContent className='space-y-3'>
              {overview?.by_status && Object.entries(overview.by_status).map(([status, count]) => (
                <div key={status} className='flex items-center justify-between'>
                  <span className='text-sm capitalize'>{status}</span>
                  <div className='flex items-center gap-2'>
                    <div className='h-2 w-24 rounded-full bg-muted overflow-hidden'>
                      <div
                        className='h-full bg-primary'
                        style={{ width: `${(count / Math.max(overview?.total_cases ?? 1, 1)) * 100}%` }}
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
              {risk?.distribution && Object.entries(risk.distribution).map(([range, count]) => (
                <div key={range} className='flex items-center justify-between'>
                  <span className='text-sm'>{range}</span>
                  <div className='flex items-center gap-2'>
                    <div className='h-2 w-24 rounded-full bg-muted overflow-hidden'>
                      <div
                        className='h-full bg-primary'
                        style={{ width: `${(count / Math.max(risk?.total ?? 1, 1)) * 100}%` }}
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
                  <div className='text-3xl font-bold text-green-500'>{sla?.on_track ?? 0}</div>
                  <p className='text-sm text-muted-foreground'>On Track</p>
                </div>
                <div className='text-center'>
                  <div className='text-3xl font-bold text-red-500'>{sla?.overdue ?? 0}</div>
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
              {overview?.verdicts && Object.entries(overview.verdicts).map(([verdict, count]) => (
                <div key={verdict} className='flex items-center justify-between'>
                  <span className='text-sm capitalize'>{verdict}</span>
                  <span className='text-sm font-medium'>{count}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {trends && trends.trends.length > 0 && (
          <Card className='mt-6'>
            <CardHeader>
              <CardTitle>Daily Trends (Last 30 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='h-64 flex items-end gap-1'>
                {trends.trends.map((day) => {
                  const maxVal = Math.max(...trends.trends.map(d => d.total), 1)
                  return (
                    <div key={day.date} className='flex-1 flex flex-col items-center gap-1' title={`${day.date}: ${day.total} cases`}>
                      <div className='w-full flex flex-col gap-0.5' style={{ height: '200px', justifyContent: 'flex-end' }}>
                        <div className='w-full bg-green-500 rounded-t' style={{ height: `${(day.approved / maxVal) * 100}%`, minHeight: day.approved > 0 ? '2px' : '0' }} />
                        <div className='w-full bg-yellow-500' style={{ height: `${(day.review / maxVal) * 100}%`, minHeight: day.review > 0 ? '2px' : '0' }} />
                        <div className='w-full bg-red-500 rounded-b' style={{ height: `${(day.rejected / maxVal) * 100}%`, minHeight: day.rejected > 0 ? '2px' : '0' }} />
                      </div>
                      <span className='text-[10px] text-muted-foreground'>{day.date.slice(5)}</span>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        )}
        </>
        )}
      </Main>
    </>
  )
}
