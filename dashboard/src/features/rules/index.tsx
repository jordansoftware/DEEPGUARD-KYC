import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { SlidersHorizontal } from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search as SearchIcon } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

interface RulesData {
  weights: Record<string, number>
  defect_weights: Record<string, number>
  thresholds: Record<string, number>
}

function Slider({ label, value, max, unit }: { label: string; value: number; max: number; unit?: string }) {
  return (
    <div className='space-y-1'>
      <div className='flex items-center justify-between'>
        <span className='text-sm text-muted-foreground'>{label}</span>
        <span className='text-sm font-mono font-medium'>
          {value}
          {unit && <span className='text-muted-foreground text-xs ml-1'>{unit}</span>}
        </span>
      </div>
      <div className='h-2 w-full rounded-full bg-muted overflow-hidden'>
        <div
          className='h-full bg-primary rounded-full'
          style={{ width: `${(value / max) * 100}%` }}
        />
      </div>
    </div>
  )
}

export function RulesPage() {
  const { data, isLoading, isError } = useQuery<RulesData>({
    queryKey: ['rules-defaults'],
    queryFn: async () => {
      return apiFetch('/rules/defaults')
    },
  })

  return (
    <>
      <Header>
        <SearchIcon className='me-auto' />
        <ThemeSwitch />
        <ProfileDropdown />
      </Header>

      <Main>
        <div className='mb-6'>
          <h1 className='text-2xl font-bold tracking-tight'>
            <SlidersHorizontal className='inline h-6 w-6 mr-2 -mt-1' />
            Rules Engine
          </h1>
          <p className='text-muted-foreground'>
            Signal weights, defect penalties and decision thresholds.
          </p>
        </div>

        {isLoading ? (
          <div className='grid gap-6 md:grid-cols-3'>
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <CardTitle className='text-lg'>Loading...</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className='space-y-3'>
                    {Array.from({ length: 4 }).map((_, j) => (
                      <div key={j} className='h-4 animate-pulse rounded bg-muted' />
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : isError ? (
          <Card>
            <CardHeader>
              <CardTitle className='text-lg text-destructive'>Failed to load rules</CardTitle>
              <CardDescription>Make sure the backend is running and the API key is configured.</CardDescription>
            </CardHeader>
          </Card>
        ) : data ? (
          <div className='grid gap-6 md:grid-cols-3'>
            <Card>
              <CardHeader>
                <CardTitle className='text-lg'>Signal Weights</CardTitle>
                <CardDescription>Contribution of each signal to the final score</CardDescription>
              </CardHeader>
              <CardContent className='space-y-4'>
                {Object.entries(data.weights).map(([key, weight]) => (
                  <Slider key={key} label={key.replace(/_/g, ' ')} value={weight} max={1} />
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className='text-lg'>Defect Penalties</CardTitle>
                <CardDescription>Score reduction for each detected defect</CardDescription>
              </CardHeader>
              <CardContent className='space-y-4 max-h-96 overflow-y-auto'>
                {Object.entries(data.defect_weights).map(([key, penalty]) => (
                  <div key={key} className='flex items-center justify-between text-sm'>
                    <span className='text-muted-foreground'>{key.replace(/_/g, ' ')}</span>
                    <Badge variant='secondary'>-{penalty}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className='text-lg'>Thresholds</CardTitle>
                <CardDescription>Decision boundaries and SLA settings</CardDescription>
              </CardHeader>
              <CardContent className='space-y-4'>
                <Slider
                  label='Auto-approve score'
                  value={data.thresholds.auto_approve_score ?? 0}
                  max={100}
                  unit='%'
                />
                <Slider
                  label='Auto-reject score'
                  value={data.thresholds.auto_reject_score ?? 0}
                  max={100}
                  unit='%'
                />
                <Slider
                  label='Face match threshold'
                  value={(data.thresholds.face_match_threshold ?? 0) * 100}
                  max={100}
                  unit='%'
                />
                <div className='flex items-center justify-between text-sm'>
                  <span className='text-muted-foreground'>SLA hours</span>
                  <span className='font-mono font-medium'>{data.thresholds.sla_hours}h</span>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </Main>
    </>
  )
}
