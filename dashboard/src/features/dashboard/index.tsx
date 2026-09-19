import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { BarChart3, Clock, FileSearch, CheckCircle2, XCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { NumberTicker } from '@/components/ui/number-ticker'
import { Overview } from './components/overview'
import { RecentCases } from './components/recent-cases'
import { Analytics } from './components/analytics'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface KycStats {
  total_cases: number
  by_status: Record<string, number>
  average_score: number
  approval_rate: number
}

export function Dashboard() {
  const { data: stats } = useQuery<KycStats>({
    queryKey: ['kyc-stats'],
    queryFn: async () => {
      return apiFetch('/analytics/overview')
    },
  })

  const totalCases = stats?.total_cases ?? 0
  const pending = stats?.by_status?.pending ?? 0
  const review = stats?.by_status?.review ?? 0
  const approved = stats?.by_status?.approved ?? 0
  const rejected = stats?.by_status?.rejected ?? 0

  return (
    <>
      <Header>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ProfileDropdown />
      </Header>

      <Main>
        <div className='mb-6'>
          <h1 className='text-3xl font-bold tracking-tight text-white'>
            DeepGuard
          </h1>
          <p className='text-muted-foreground'>
            KYC verification platform — monitor cases, scores and compliance.
          </p>
        </div>

        <div className='mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5'>
          <Card>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-medium'>Total Cases</CardTitle>
              <FileSearch className='h-4 w-4 text-muted-foreground' />
            </CardHeader>
            <CardContent>
              <div className='text-2xl font-bold'>
                <NumberTicker value={totalCases} />
              </div>
              <p className='text-xs text-muted-foreground'>All submitted cases</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-medium'>Pending</CardTitle>
              <Clock className='h-4 w-4 text-yellow-500' />
            </CardHeader>
            <CardContent>
              <div className='text-2xl font-bold'>
                <NumberTicker value={pending} />
              </div>
              <p className='text-xs text-muted-foreground'>Awaiting review</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-medium'>In Review</CardTitle>
              <BarChart3 className='h-4 w-4 text-blue-500' />
            </CardHeader>
            <CardContent>
              <div className='text-2xl font-bold'>
                <NumberTicker value={review} />
              </div>
              <p className='text-xs text-muted-foreground'>Under manual review</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-medium'>Approved</CardTitle>
              <CheckCircle2 className='h-4 w-4 text-green-500' />
            </CardHeader>
            <CardContent>
              <div className='text-2xl font-bold'>
                <NumberTicker value={approved} />
              </div>
              <p className='text-xs text-muted-foreground'>
                {totalCases > 0 ? Math.round((approved / totalCases) * 100) : 0}% approval rate
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-medium'>Rejected</CardTitle>
              <XCircle className='h-4 w-4 text-red-500' />
            </CardHeader>
            <CardContent>
              <div className='text-2xl font-bold'>
                <NumberTicker value={rejected} />
              </div>
              <p className='text-xs text-muted-foreground'>Flagged as forged</p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue='overview' className='space-y-4'>
          <TabsList>
            <TabsTrigger value='overview'>Overview</TabsTrigger>
            <TabsTrigger value='analytics'>Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value='overview' className='space-y-4'>
            <div className='grid grid-cols-1 gap-4 lg:grid-cols-7'>
              <Card className='col-span-1 lg:col-span-4'>
                <CardHeader>
                  <CardTitle>Case Trends</CardTitle>
                  <CardDescription>Daily KYC submissions (last 30 days)</CardDescription>
                </CardHeader>
                <CardContent>
                  <Overview />
                </CardContent>
              </Card>

              <Card className='col-span-1 lg:col-span-3'>
                <CardHeader>
                  <CardTitle>Recent Cases</CardTitle>
                  <CardDescription>Latest submitted KYC cases</CardDescription>
                </CardHeader>
                <CardContent>
                  <RecentCases />
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value='analytics' className='space-y-4'>
            <Analytics />
          </TabsContent>
        </Tabs>
      </Main>
    </>
  )
}
