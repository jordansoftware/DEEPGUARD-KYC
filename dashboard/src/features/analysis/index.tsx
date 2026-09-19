import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
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
import { Eye } from 'lucide-react'
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
import { DataTableColumnHeader } from '@/components/data-table'
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

interface CaseDetail extends Case {
  signals?: Record<string, unknown>
  badges?: string[]
  analysis?: Record<string, unknown>
}

function ScoreCell({ score }: { score: number }) {
  let color = 'text-green-600'
  if (score < 50) color = 'text-red-600'
  else if (score < 80) color = 'text-yellow-600'

  return (
    <span className={`font-semibold ${color}`}>
      {score}
    </span>
  )
}

export function AnalysisResults() {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = useState({})
  const [globalFilter, setGlobalFilter] = useState('')
  const [selectedCase, setSelectedCase] = useState<Case | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  const { data, isLoading } = useQuery<CasesResponse>({
    queryKey: ['analysis-cases'],
    queryFn: async () => {
      return apiFetch('/kyc/cases?page_size=100')
    },
  })

  const { data: detailData, isLoading: detailLoading } = useQuery<CaseDetail>({
    queryKey: ['analysis-case-detail', selectedCase?.id],
    queryFn: async () => {
      return apiFetch(`/kyc/cases/${selectedCase?.id}`)
    },
    enabled: !!selectedCase?.id && detailOpen,
  })

  const columns: ColumnDef<Case>[] = [
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
      accessorKey: 'score',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title='Score' />
      ),
      cell: ({ row }) => <ScoreCell score={row.getValue('score')} />,
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
      cell: ({ row }) => {
        const status = row.getValue('status') as string
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
      },
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
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => (
        <Button
          variant='ghost'
          size='sm'
          onClick={() => {
            setSelectedCase(row.original)
            setDetailOpen(true)
          }}
        >
          <Eye className='h-4 w-4' />
        </Button>
      ),
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
          <h1 className='text-2xl font-bold tracking-tight'>Analysis Results</h1>
          <p className='text-muted-foreground'>
            Review document analysis scores and verdicts.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='mb-4'>
              <Input
                placeholder='Search results...'
                value={globalFilter}
                onChange={(e) => setGlobalFilter(e.target.value)}
                className='max-w-sm'
              />
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
                        No results found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            <div className='mt-4 flex items-center justify-between'>
              <p className='text-sm text-muted-foreground'>
                {table.getFilteredRowModel().rows.length} result(s) total
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

        <Sheet open={detailOpen} onOpenChange={setDetailOpen}>
          <SheetContent className='w-full sm:max-w-lg overflow-y-auto'>
            <SheetHeader>
              <SheetTitle>Analysis Detail</SheetTitle>
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
                    <ScoreCell score={detailData.score} />
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

                {detailData.analysis && Object.keys(detailData.analysis).length > 0 && (
                  <div>
                    <p className='text-sm font-medium text-muted-foreground mb-2'>Full Analysis</p>
                    <div className='rounded-md border p-3'>
                      <pre className='text-xs overflow-auto'>
                        {JSON.stringify(detailData.analysis, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </SheetContent>
        </Sheet>
      </Main>
    </>
  )
}
