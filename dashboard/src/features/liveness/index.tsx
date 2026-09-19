import { useState } from 'react'
import { apiFetch } from '@/lib/api'
import {
  Camera,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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

interface LivenessResult {
  score: number
  passed: boolean
  signals: Record<string, { score: number; note: string }>
  reasons: string[]
  verdict: string
}

export function LivenessDetection() {
  const [caseId, setCaseId] = useState('')
  const [result, setResult] = useState<LivenessResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleCheck = async () => {
    if (!caseId) return
    setLoading(true)
    try {
      const data = await apiFetch(`/kyc/cases/${caseId}`)
      if (data.documents?.[0]?.signals) {
        setResult({
          score: data.score / 100,
          passed: data.status === 'approved',
          signals: {},
          reasons: data.reasons || [],
          verdict: data.verdict,
        })
      }
    } catch {
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Header>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ProfileDropdown />
      </Header>
      <Main>
        <div className='mb-6'>
          <h1 className='text-2xl font-bold tracking-tight'>Liveness Detection</h1>
          <p className='text-muted-foreground'>
            Anti-spoofing analysis for selfie uploads. Detects printed photos, screen replays, and masks.
          </p>
        </div>

        <Card className='mb-6'>
          <CardHeader>
            <CardTitle>Check Liveness</CardTitle>
            <CardDescription>Enter a case ID to view liveness analysis results</CardDescription>
          </CardHeader>
          <CardContent>
            <div className='flex gap-4'>
              <input
                type='text'
                placeholder='Case ID'
                value={caseId}
                onChange={(e) => setCaseId(e.target.value)}
                className='flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm'
              />
              <Button onClick={handleCheck} disabled={loading || !caseId}>
                {loading ? <RefreshCw className='mr-2 h-4 w-4 animate-spin' /> : <Camera className='mr-2 h-4 w-4' />}
                Analyze
              </Button>
            </div>
          </CardContent>
        </Card>

        {result && (
          <div className='grid gap-6 md:grid-cols-2'>
            <Card>
              <CardHeader>
                <CardTitle className='flex items-center gap-2'>
                  {result.passed ? (
                    <CheckCircle2 className='h-5 w-5 text-green-500' />
                  ) : (
                    <XCircle className='h-5 w-5 text-red-500' />
                  )}
                  Liveness Score: {Math.round(result.score * 100)}%
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Badge variant={result.passed ? 'default' : 'destructive'} className='mb-4'>
                  {result.passed ? 'PASSED — Live Person' : 'FAILED — Possible Spoof'}
                </Badge>
                {result.reasons.length > 0 && (
                  <div className='space-y-2'>
                    <p className='text-sm font-medium'>Issues:</p>
                    {result.reasons.map((r, i) => (
                      <div key={i} className='flex items-start gap-2 text-sm text-muted-foreground'>
                        <AlertTriangle className='mt-0.5 h-3 w-3 text-yellow-500 shrink-0' />
                        {r}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Signal Breakdown</CardTitle>
              </CardHeader>
              <CardContent className='space-y-4'>
                {Object.entries(result.signals).map(([key, signal]) => (
                  <div key={key}>
                    <div className='flex items-center justify-between mb-1'>
                      <span className='text-sm font-medium capitalize'>{key.replace('_', ' ')}</span>
                      <span className='text-sm text-muted-foreground'>{Math.round(signal.score * 100)}%</span>
                    </div>
                    <div className='h-2 rounded-full bg-muted overflow-hidden'>
                      <div
                        className={`h-full rounded-full transition-all ${
                          signal.score >= 0.6 ? 'bg-green-500' : signal.score >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${signal.score * 100}%` }}
                      />
                    </div>
                    <p className='text-xs text-muted-foreground mt-1'>{signal.note}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        )}
      </Main>
    </>
  )
}
