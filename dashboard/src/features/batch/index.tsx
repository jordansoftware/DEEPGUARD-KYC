import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import {
  Upload,
  CheckCircle2,
  Clock,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

interface BatchJob {
  id: number
  status: string
  total_files: number
  processed: number
  failed: number
  case_ids: number[]
  created_at: string
}

export function BatchUpload() {
  const [files, setFiles] = useState<FileList | null>(null)
  const [applicant, setApplicant] = useState('')
  const [docType, setDocType] = useState('cni')
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery<{ batches: BatchJob[]; total: number }>({
    queryKey: ['batches'],
    queryFn: async () => {
      return apiFetch('/batch/?page_size=50')
    },
  })

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!files) return
      const formData = new FormData()
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i])
      }
      formData.append('applicant', applicant)
      formData.append('doc_type', docType)
      return apiFetch('/batch/upload', { method: 'POST', body: formData })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] })
      setFiles(null)
      setApplicant('')
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
          <h1 className='text-2xl font-bold tracking-tight'>Batch Upload</h1>
          <p className='text-muted-foreground'>
            Upload multiple documents for batch KYC processing.
          </p>
        </div>

        <Card className='mb-6'>
          <CardHeader>
            <CardTitle>Upload Files</CardTitle>
            <CardDescription>Select multiple document images to process in batch</CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid gap-4 md:grid-cols-2'>
              <div>
                <label className='text-sm font-medium'>Applicant Name</label>
                <input
                  type='text'
                  placeholder='Applicant name'
                  value={applicant}
                  onChange={(e) => setApplicant(e.target.value)}
                  className='mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm'
                />
              </div>
              <div>
                <label className='text-sm font-medium'>Document Type</label>
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className='mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm'
                >
                  <option value='cni'>ID Card</option>
                  <option value='passeport'>Passport</option>
                  <option value='selfie'>Selfie</option>
                  <option value='justificatif'>Proof of Address</option>
                  <option value='permis'>Driver License</option>
                </select>
              </div>
            </div>
            <div>
              <label className='text-sm font-medium'>Documents</label>
              <input
                type='file'
                multiple
                accept='image/*'
                onChange={(e) => setFiles(e.target.files)}
                className='mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/80'
              />
              {files && (
                <p className='mt-2 text-sm text-muted-foreground'>
                  {files.length} file(s) selected
                </p>
              )}
            </div>
            <Button
              onClick={() => uploadMutation.mutate()}
              disabled={!files || files.length === 0 || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? (
                <RefreshCw className='mr-2 h-4 w-4 animate-spin' />
              ) : (
                <Upload className='mr-2 h-4 w-4' />
              )}
              Process Batch ({files?.length || 0} files)
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Batch History</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className='space-y-2'>
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className='h-12 animate-pulse rounded bg-muted' />
                ))}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Batch ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Files</TableHead>
                    <TableHead>Processed</TableHead>
                    <TableHead>Failed</TableHead>
                    <TableHead>Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.batches?.map((batch) => (
                    <TableRow key={batch.id}>
                      <TableCell className='font-medium'>#{batch.id}</TableCell>
                      <TableCell>
                        <Badge variant={batch.status === 'completed' ? 'default' : 'secondary'}>
                          {batch.status === 'completed' ? (
                            <CheckCircle2 className='mr-1 h-3 w-3' />
                          ) : (
                            <Clock className='mr-1 h-3 w-3' />
                          )}
                          {batch.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{batch.total_files}</TableCell>
                      <TableCell className='text-green-600'>{batch.processed}</TableCell>
                      <TableCell className={batch.failed > 0 ? 'text-red-600' : ''}>{batch.failed}</TableCell>
                      <TableCell>{new Date(batch.created_at).toLocaleDateString()}</TableCell>
                    </TableRow>
                  ))}
                  {(!data?.batches || data.batches.length === 0) && (
                    <TableRow>
                      <TableCell colSpan={6} className='h-24 text-center'>No batch jobs yet.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
