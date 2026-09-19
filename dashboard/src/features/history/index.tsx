import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { CheckCircle2, Eye, XCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

interface Case {
  id: string
  applicant: string
  doc_type: string
  country: string
  submitted: string
  score: number
  verdict: string
  status: string
}

interface CasesResponse {
  cases: Case[]
  total: number
  page: number
  page_size: number
}

function VerdictIcon({ verdict }: { verdict: string }) {
  switch (verdict) {
    case 'pass':
      return <CheckCircle2 className='h-5 w-5 text-green-500' />
    case 'fail':
      return <XCircle className='h-5 w-5 text-red-500' />
    default:
      return <Eye className='h-5 w-5 text-yellow-500' />
  }
}

export function HistoryPage() {
  const [search, setSearch] = useState('')
  const [verdictFilter, setVerdictFilter] = useState<string>('all')

  const { data, isLoading } = useQuery<CasesResponse>({
    queryKey: ['history-cases', verdictFilter],
    queryFn: async () => {
      return apiFetch('/kyc/cases?page_size=100')
    },
  })

  const filteredCases = (data?.cases || []).filter((c) => {
    const matchesSearch =
      search === '' ||
      c.applicant.toLowerCase().includes(search.toLowerCase()) ||
      c.id.toLowerCase().includes(search.toLowerCase())
    const matchesVerdict =
      verdictFilter === 'all' || c.verdict === verdictFilter
    return matchesSearch && matchesVerdict
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
          <h1 className='text-2xl font-bold tracking-tight'>History</h1>
          <p className='text-muted-foreground'>
            View all case decisions and their outcomes.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Decision History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='mb-6 flex items-center gap-4'>
              <Input
                placeholder='Search by applicant or ID...'
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className='max-w-sm'
              />
              <Select value={verdictFilter} onValueChange={setVerdictFilter}>
                <SelectTrigger className='w-[180px]'>
                  <SelectValue placeholder='Filter by verdict' />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value='all'>All Verdicts</SelectItem>
                  <SelectItem value='pass'>Pass</SelectItem>
                  <SelectItem value='fail'>Fail</SelectItem>
                  <SelectItem value='manual'>Manual Review</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {isLoading ? (
              <div className='space-y-4'>
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className='h-16 animate-pulse rounded bg-muted' />
                ))}
              </div>
            ) : filteredCases.length === 0 ? (
              <div className='py-12 text-center text-muted-foreground'>
                No cases found.
              </div>
            ) : (
              <div className='space-y-3'>
                {filteredCases.map((c) => (
                  <div
                    key={c.id}
                    className='flex items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-muted/50'
                  >
                    <VerdictIcon verdict={c.verdict} />
                    <div className='flex-1 min-w-0'>
                      <div className='flex items-center gap-2'>
                        <span className='font-medium truncate'>
                          {c.applicant}
                        </span>
                        <Badge variant='outline' className='text-xs'>
                          {c.doc_type}
                        </Badge>
                      </div>
                      <p className='text-sm text-muted-foreground truncate'>
                        {c.id}
                      </p>
                    </div>
                    <div className='flex items-center gap-4 text-sm text-muted-foreground'>
                      <span className='font-semibold'>
                        Score: {c.score}
                      </span>
                      <Badge
                        variant={
                          c.verdict === 'pass'
                            ? 'default'
                            : c.verdict === 'fail'
                              ? 'destructive'
                              : 'secondary'
                        }
                      >
                        {c.verdict}
                      </Badge>
                      <span className='whitespace-nowrap'>
                        {new Date(c.submitted).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className='mt-4 text-sm text-muted-foreground'>
              Showing {filteredCases.length} of {data?.total ?? 0} cases
            </div>
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
