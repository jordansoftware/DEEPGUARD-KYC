import { useState } from 'react'
import { Download, FileText, Table } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card'
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

export function ExportPage() {
  const [format, setFormat] = useState('csv')
  const [status, setStatus] = useState('all')

  const handleExport = () => {
    const params = new URLSearchParams({ format })
    if (status !== 'all') params.set('status', status)
    window.open(`/api/export/cases?${params}`, '_blank')
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
          <h1 className='text-2xl font-bold tracking-tight'>Export Data</h1>
          <p className='text-muted-foreground'>
            Export KYC cases as CSV or Excel files.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Export Options</CardTitle>
            <CardDescription>Choose format and filters for your export</CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid gap-4 md:grid-cols-2'>
              <div>
                <label className='text-sm font-medium'>Format</label>
                <Select value={format} onValueChange={setFormat}>
                  <SelectTrigger className='mt-1'>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value='csv'>
                      <div className='flex items-center gap-2'>
                        <FileText className='h-4 w-4' />
                        CSV
                      </div>
                    </SelectItem>
                    <SelectItem value='xlsx'>
                      <div className='flex items-center gap-2'>
                        <Table className='h-4 w-4' />
                        Excel (XLSX)
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className='text-sm font-medium'>Status Filter</label>
                <Select value={status} onValueChange={setStatus}>
                  <SelectTrigger className='mt-1'>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value='all'>All Statuses</SelectItem>
                    <SelectItem value='pending'>Pending</SelectItem>
                    <SelectItem value='review'>Under Review</SelectItem>
                    <SelectItem value='approved'>Approved</SelectItem>
                    <SelectItem value='rejected'>Rejected</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button onClick={handleExport} size='lg'>
              <Download className='mr-2 h-4 w-4' />
              Export {format.toUpperCase()}
            </Button>
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
