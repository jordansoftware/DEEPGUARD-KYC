import { useState } from 'react'
import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query'
import {
  type ColumnDef,
  type SortingState,
  type VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import {
  CheckCircle2,
  Clock,
  Eye,
  FileSearch,
  Filter,
  XCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DataTableColumnHeader,
} from '@/components/data-table'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { apiFetch } from '@/lib/api'

interface KYCCase {
  id: string
  applicant: string
  doc_type: string
  country: string
  submitted: string
  score: number
  verdict: string
  status: string
  reference?: string
  signals?: Record<string, unknown>
  badges?: string[]
}

interface KYCResponse {
  cases: KYCCase[]
  total: number
  page: number
  page_size: number
  stats: {
    total: number
    pending: number
    review: number
    approved: number
    rejected: number
  }
}

interface KYCDetailResponse extends KYCCase {
  signals?: Record<string, unknown>
  badges?: string[]
  analysis?: Record<string, unknown>
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string
  value: number | string
  icon: React.ComponentType<{ className?: string }>
  color: string
}) {
  return (
    <Card>
      <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
        <CardTitle className='text-sm font-medium'>{title}</CardTitle>
        <Icon className={`h-4 w-4 ${color}`} />
      </CardHeader>
      <CardContent>
        <div className='text-2xl font-bold'>{value}</div>
      </CardContent>
    </Card>
  )
}

function ScoreBadge({ score }: { score: number }) {
  if (score >= 80) {
    return (
      <Badge variant='default' className='bg-green-600 hover:bg-green-700'>
        {score}
      </Badge>
    )
  }
  if (score >= 50) {
    return (
      <Badge variant='default' className='bg-yellow-500 hover:bg-yellow-600 text-black'>
        {score}
      </Badge>
    )
  }
  return <Badge variant='destructive'>{score}</Badge>
}

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    review: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    approved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  }
  return (
    <Badge variant='secondary' className={variants[status] || ''}>
      {status}
    </Badge>
  )
}

export function KYCDashboard() {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = useState({})
  const [globalFilter, setGlobalFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedCase, setSelectedCase] = useState<KYCCase | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  const queryClient = useQueryClient()

  const { data, isLoading, isError: isKycError } = useQuery<KYCResponse>({
    queryKey: ['kyc-cases', statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams({ page: '1', page_size: '100' })
      if (statusFilter !== 'all') params.set('status', statusFilter)
      return apiFetch(`/kyc/cases?${params}`)
    },
  })

  const { data: detailData, isLoading: detailLoading } = useQuery<KYCDetailResponse>({
    queryKey: ['kyc-case-detail', selectedCase?.id],
    queryFn: async () => {
      return apiFetch(`/kyc/cases/${selectedCase?.id}`)
    },
    enabled: !!selectedCase?.id && detailOpen,
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, status, notes }: { id: string; status: string; notes?: string }) => {
      return apiFetch(`/kyc/cases/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status, notes }),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kyc-cases'] })
      setDetailOpen(false)
      setSelectedCase(null)
    },
  })

  const columns: ColumnDef<KYCCase>[] = [
    {
      accessorKey: 'applicant',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title='Applicant' />
      ),
      cell: ({ row }) => (
        <span className='font-medium'>{row.getValue('applicant')}</span>
      ),
    },
    {
      accessorKey: 'doc_type',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title='Doc Type' />
      ),
    },
    {
      accessorKey: 'country',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title='Country' />
      ),
    },
    {
      accessorKey: 'submitted',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title='Submitted' />
      ),
      cell: ({ row }) => {
        const date = new Date(row.getValue('submitted'))
        return date.toLocaleDateString()
      },
    },
    {
      accessorKey: 'score',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title='Score' />
      ),
      cell: ({ row }) => <ScoreBadge score={row.getValue('score')} />,
    },
    {
      accessorKey: 'verdict',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title='Verdict' />
      ),
      cell: ({ row }) => {
        const verdict = row.getValue('verdict') as string
        const variant =
          verdict === 'pass'
            ? 'default'
            : verdict === 'fail'
              ? 'destructive'
              : 'secondary'
        return <Badge variant={variant}>{verdict}</Badge>
      },
    },
    {
      accessorKey: 'status',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title='Status' />
      ),
      cell: ({ row }) => <StatusBadge status={row.getValue('status')} />,
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const kycCase = row.original
        return (
          <Button
            variant='ghost'
            size='sm'
            onClick={() => {
              setSelectedCase(kycCase)
              setDetailOpen(true)
            }}
          >
            <Eye className='h-4 w-4' />
          </Button>
        )
      },
    },
  ]

  const table = useReactTable({
    data: data?.cases || [],
    columns,
    onSortingChange: setSorting,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    state: {
      sorting,
      columnVisibility,
      rowSelection,
      globalFilter,
    },
    onGlobalFilterChange: setGlobalFilter,
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
          <h1 className='text-2xl font-bold tracking-tight'>KYC Dashboard</h1>
          <p className='text-muted-foreground'>
            Monitor and manage Know Your Customer verification cases.
          </p>
        </div>

        <div className='mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5'>
          <StatCard
            title='Total Cases'
            value={data?.stats.total ?? 0}
            icon={FileSearch}
            color='text-muted-foreground'
          />
          <StatCard
            title='Pending'
            value={data?.stats.pending ?? 0}
            icon={Clock}
            color='text-yellow-500'
          />
          <StatCard
            title='Under Review'
            value={data?.stats.review ?? 0}
            icon={Eye}
            color='text-blue-500'
          />
          <StatCard
            title='Approved'
            value={data?.stats.approved ?? 0}
            icon={CheckCircle2}
            color='text-green-500'
          />
          <StatCard
            title='Rejected'
            value={data?.stats.rejected ?? 0}
            icon={XCircle}
            color='text-red-500'
          />
        </div>

        {isKycError ? (
          <Card>
            <CardHeader>
              <CardTitle className='text-destructive'>Failed to load KYC cases</CardTitle>
            </CardHeader>
            <CardContent>
              <p className='text-sm text-muted-foreground'>
                Check that the backend is running and your API key is configured in Settings.
              </p>
            </CardContent>
          </Card>
        ) : (
        <Card>
          <CardHeader>
            <CardTitle>KYC Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='mb-4 flex items-center gap-4'>
              <Input
                placeholder='Search cases...'
                value={globalFilter}
                onChange={(e) => setGlobalFilter(e.target.value)}
                className='max-w-sm'
              />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className='w-[180px]'>
                  <Filter className='mr-2 h-4 w-4' />
                  <SelectValue placeholder='Filter by status' />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value='all'>All Statuses</SelectItem>
                  <SelectItem value='pending'>Pending</SelectItem>
                  <SelectItem value='review'>Review</SelectItem>
                  <SelectItem value='approved'>Approved</SelectItem>
                  <SelectItem value='rejected'>Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className='rounded-md border'>
              <Table>
                <TableHeader>
                  {table.getHeaderGroups().map((headerGroup) => (
                    <TableRow key={headerGroup.id}>
                      {headerGroup.headers.map((header) => (
                        <TableHead key={header.id}>
                          {header.isPlaceholder
                            ? null
                            : flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                              )}
                        </TableHead>
                      ))}
                    </TableRow>
                  ))}
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    Array.from({ length: 5 }).map((_, i) => (
                      <TableRow key={i}>
                        {columns.map((_, j) => (
                          <TableCell key={j}>
                            <div className='h-4 animate-pulse rounded bg-muted' />
                          </TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : table.getRowModel().rows?.length ? (
                    table.getRowModel().rows.map((row) => (
                      <TableRow
                        key={row.id}
                        data-state={row.getIsSelected() && 'selected'}
                        className='cursor-pointer'
                        onClick={() => {
                          setSelectedCase(row.original)
                          setDetailOpen(true)
                        }}
                      >
                        {row.getVisibleCells().map((cell) => (
                          <TableCell key={cell.id}>
                            {flexRender(
                              cell.column.columnDef.cell,
                              cell.getContext()
                            )}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={columns.length}
                        className='h-24 text-center'
                      >
                        No cases found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            <div className='mt-4 flex items-center justify-between'>
              <p className='text-sm text-muted-foreground'>
                {table.getFilteredRowModel().rows.length} case(s) total
              </p>
              <div className='flex items-center gap-2'>
                <Button
                  variant='outline'
                  size='sm'
                  onClick={() => table.previousPage()}
                  disabled={!table.getCanPreviousPage()}
                >
                  Previous
                </Button>
                <span className='text-sm'>
                  Page {table.getState().pagination.pageIndex + 1} of{' '}
                  {table.getPageCount()}
                </span>
                <Button
                  variant='outline'
                  size='sm'
                  onClick={() => table.nextPage()}
                  disabled={!table.getCanNextPage()}
                >
                  Next
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        )}

        <Sheet open={detailOpen} onOpenChange={setDetailOpen}>
          <SheetContent className='w-full sm:max-w-lg overflow-y-auto'>
            <SheetHeader>
              <SheetTitle>Case Detail</SheetTitle>
              <SheetDescription>
                {selectedCase?.applicant} - {selectedCase?.id}
              </SheetDescription>
            </SheetHeader>
            {detailLoading ? (
              <div className='space-y-4 p-4'>
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className='h-10 animate-pulse rounded bg-muted' />
                ))}
              </div>
            ) : detailData ? (
              <div className='space-y-6 p-4'>
                <div className='grid grid-cols-2 gap-4'>
                  <div>
                    <p className='text-sm font-medium text-muted-foreground'>Applicant</p>
                    <p className='text-sm'>{detailData.applicant}</p>
                  </div>
                  <div>
                    <p className='text-sm font-medium text-muted-foreground'>Document Type</p>
                    <p className='text-sm'>{detailData.doc_type}</p>
                  </div>
                  <div>
                    <p className='text-sm font-medium text-muted-foreground'>Country</p>
                    <p className='text-sm'>{detailData.country}</p>
                  </div>
                  <div>
                    <p className='text-sm font-medium text-muted-foreground'>Submitted</p>
                    <p className='text-sm'>
                      {new Date(detailData.submitted).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className='text-sm font-medium text-muted-foreground'>Score</p>
                    <ScoreBadge score={detailData.score} />
                  </div>
                  <div>
                    <p className='text-sm font-medium text-muted-foreground'>Verdict</p>
                    <Badge
                      variant={
                        detailData.verdict === 'pass'
                          ? 'default'
                          : detailData.verdict === 'fail'
                            ? 'destructive'
                            : 'secondary'
                      }
                    >
                      {detailData.verdict}
                    </Badge>
                  </div>
                  <div>
                    <p className='text-sm font-medium text-muted-foreground'>Status</p>
                    <StatusBadge status={detailData.status} />
                  </div>
                  {detailData.reference && (
                    <div>
                      <p className='text-sm font-medium text-muted-foreground'>Reference</p>
                      <p className='text-sm'>{detailData.reference}</p>
                    </div>
                  )}
                </div>

                {detailData.badges && detailData.badges.length > 0 && (
                  <div>
                    <p className='text-sm font-medium text-muted-foreground mb-2'>Badges</p>
                    <div className='flex flex-wrap gap-2'>
                      {detailData.badges.map((badge) => (
                        <Badge key={badge} variant='outline'>
                          {badge}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {detailData.signals && Object.keys(detailData.signals).length > 0 && (
                  <div>
                    <p className='text-sm font-medium text-muted-foreground mb-2'>Signals</p>
                    <div className='rounded-md border p-3'>
                      <pre className='text-xs overflow-auto'>
                        {JSON.stringify(detailData.signals, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Face Verification Section */}
                <FaceVerificationSection caseId={Number(detailData.id)} caseData={detailData} />

                <div className='flex gap-2 pt-4'>
                  <Button
                    variant='default'
                    className='flex-1 bg-green-600 hover:bg-green-700'
                    onClick={() =>
                      updateMutation.mutate({
                        id: detailData.id,
                        status: 'approved',
                      })
                    }
                    disabled={updateMutation.isPending}
                  >
                    <CheckCircle2 className='mr-2 h-4 w-4' />
                    Approve
                  </Button>
                  <Button
                    variant='outline'
                    className='flex-1'
                    onClick={() =>
                      updateMutation.mutate({
                        id: detailData.id,
                        status: 'review',
                      })
                    }
                    disabled={updateMutation.isPending}
                  >
                    <Eye className='mr-2 h-4 w-4' />
                    Review
                  </Button>
                  <Button
                    variant='destructive'
                    className='flex-1'
                    onClick={() =>
                      updateMutation.mutate({
                        id: detailData.id,
                        status: 'rejected',
                      })
                    }
                    disabled={updateMutation.isPending}
                  >
                    <XCircle className='mr-2 h-4 w-4' />
                    Reject
                  </Button>
                </div>
              </div>
            ) : null}
           </SheetContent>
        </Sheet>
      </Main>
    </>
  )
}

function FaceVerificationSection({ caseId, caseData }: { caseId: number; caseData: any }) {
  const hasFaceData = caseData?.signals?.face_match !== undefined

  return (
    <div className='space-y-3'>
      <p className='text-sm font-medium text-muted-foreground'>Face Verification</p>

      {hasFaceData ? (
        <div className='rounded-md border p-3 space-y-2 text-sm'>
          <div className='flex justify-between'>
            <span>Face Match</span>
            <Badge variant={caseData.signals.face_match ? 'default' : 'destructive'}>
              {caseData.signals.face_match ? 'Matched' : 'Not Matched'}
            </Badge>
          </div>
          {caseData.signals.face_score !== undefined && (
            <div className='flex justify-between'>
              <span>Face Score</span>
              <span>{(caseData.signals.face_score * 100).toFixed(0)}%</span>
            </div>
          )}
          {caseData.signals.liveness && (
            <div className='flex justify-between'>
              <span>Liveness</span>
              <Badge variant={caseData.signals.liveness.is_live ? 'default' : 'destructive'}>
                {caseData.signals.liveness.is_live ? 'Live' : 'Spoof'}
              </Badge>
            </div>
          )}
          {caseData.signals.capture_device && (
            <div className='flex justify-between'>
              <span>Device</span>
              <span>{caseData.signals.capture_device}</span>
            </div>
          )}
        </div>
      ) : (
        <div className='text-sm text-muted-foreground'>
          No face verification yet. The caller app will trigger this via the
          API endpoint{' '}
          <code className='rounded bg-muted px-1 py-0.5 text-xs'>
            /api/kyc/cases/{caseId}/face-session
          </code>
          .
        </div>
      )}
    </div>
  )
}
