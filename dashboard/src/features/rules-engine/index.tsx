import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Save,
  RotateCcw,
  CheckCircle2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
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

interface RulesConfig {
  weights: Record<string, number>
  defect_weights: Record<string, number>
  thresholds: Record<string, number>
}

export function RulesEngine() {
  const [rules, setRules] = useState<RulesConfig | null>(null)
  const [saved, setSaved] = useState(false)

  const { data, isLoading, isError } = useQuery<RulesConfig>({
    queryKey: ['rules-defaults'],
    queryFn: async () => {
      return apiFetch('/rules/defaults')
    },
  })

  useEffect(() => {
    if (data && !rules) setRules(data)
  }, [data])

  const saveMutation = useMutation({
    mutationFn: async () => {
      return apiFetch('/rules/client/1', {
        method: 'PUT',
        body: JSON.stringify({
          weights: rules?.weights,
          defect_weights: rules?.defect_weights,
          thresholds: rules?.thresholds,
        }),
      })
    },
    onSuccess: () => {
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    },
  })

  const updateWeight = (key: string, value: number) => {
    if (!rules) return
    setRules({ ...rules, weights: { ...rules.weights, [key]: value } })
  }

  const updateDefectWeight = (key: string, value: number) => {
    if (!rules) return
    setRules({ ...rules, defect_weights: { ...rules.defect_weights, [key]: value } })
  }

  const updateThreshold = (key: string, value: number) => {
    if (!rules) return
    setRules({ ...rules, thresholds: { ...rules.thresholds, [key]: value } })
  }

  if (isLoading) {
    return (
      <Main>
        <div className='flex h-64 items-center justify-center text-muted-foreground'>
          Loading rules...
        </div>
      </Main>
    )
  }

  if (isError || !rules) {
    return (
      <>
        <Header>
          <Search className='me-auto' />
          <ThemeSwitch />
          <ProfileDropdown />
        </Header>
        <Main>
          <div className='mb-6'>
            <h1 className='text-2xl font-bold tracking-tight'>Rules Engine</h1>
          </div>
          <div className='rounded-md border p-6 text-center text-sm text-muted-foreground'>
            Failed to load rules. Please check your API key settings.
          </div>
        </Main>
      </>
    )
  }

  return (
    <>
      <Header>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ProfileDropdown />
      </Header>
      <Main>
        <div className='mb-6 flex items-center justify-between'>
          <div>
            <h1 className='text-2xl font-bold tracking-tight'>Analysis Rules</h1>
            <p className='text-muted-foreground'>
              Configure signal weights, defect penalties, and decision thresholds.
            </p>
          </div>
          <div className='flex gap-2'>
            <Button variant='outline' onClick={() => setRules(data || null)}>
              <RotateCcw className='mr-2 h-4 w-4' />
              Reset
            </Button>
            <Button onClick={() => saveMutation.mutate()}>
              {saved ? <CheckCircle2 className='mr-2 h-4 w-4' /> : <Save className='mr-2 h-4 w-4' />}
              {saved ? 'Saved!' : 'Save Rules'}
            </Button>
          </div>
        </div>

        <div className='grid gap-6 md:grid-cols-2'>
          <Card>
            <CardHeader>
              <CardTitle>Signal Weights</CardTitle>
              <CardDescription>How much each signal contributes to the overall score (sum = 1.0)</CardDescription>
            </CardHeader>
            <CardContent className='space-y-4'>
              {Object.entries(rules.weights).map(([key, value]) => (
                <div key={key}>
                  <div className='flex items-center justify-between mb-1'>
                    <label className='text-sm font-medium capitalize'>{key.replace('_', ' ')}</label>
                    <span className='text-sm text-muted-foreground'>{Math.round(value * 100)}%</span>
                  </div>
                  <input
                    type='range'
                    min='0'
                    max='100'
                    value={Math.round(value * 100)}
                    onChange={(e) => updateWeight(key, parseInt(e.target.value) / 100)}
                    className='w-full'
                  />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Defect Penalties</CardTitle>
              <CardDescription>Points deducted for each type of defect detected</CardDescription>
            </CardHeader>
            <CardContent className='space-y-4'>
              {Object.entries(rules.defect_weights).map(([key, value]) => (
                <div key={key}>
                  <div className='flex items-center justify-between mb-1'>
                    <label className='text-sm font-medium'>{key.replace(/_/g, ' ')}</label>
                    <span className='text-sm text-muted-foreground'>-{value} pts</span>
                  </div>
                  <input
                    type='range'
                    min='0'
                    max='10'
                    value={value}
                    onChange={(e) => updateDefectWeight(key, parseInt(e.target.value))}
                    className='w-full'
                  />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Decision Thresholds</CardTitle>
              <CardDescription>Score thresholds for auto-approve, auto-reject, and SLA</CardDescription>
            </CardHeader>
            <CardContent className='space-y-4'>
              {Object.entries(rules.thresholds).map(([key, value]) => (
                <div key={key}>
                  <div className='flex items-center justify-between mb-1'>
                    <label className='text-sm font-medium'>{key.replace(/_/g, ' ')}</label>
                    <span className='text-sm text-muted-foreground'>{value}</span>
                  </div>
                  <input
                    type='range'
                    min='0'
                    max='100'
                    value={value}
                    onChange={(e) => updateThreshold(key, parseInt(e.target.value))}
                    className='w-full'
                  />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </Main>
    </>
  )
}
