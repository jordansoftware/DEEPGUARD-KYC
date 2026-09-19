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
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

interface Endpoint {
  method: string
  path: string
  description: string
}

interface EndpointGroup {
  title: string
  description: string
  endpoints: Endpoint[]
}

const endpointGroups: EndpointGroup[] = [
  {
    title: 'Health & Status',
    description: 'System health and status monitoring.',
    endpoints: [
      {
        method: 'GET',
        path: '/api/health',
        description: 'Returns system health status and component health.',
      },
    ],
  },
  {
    title: 'Document Analysis',
    description: 'Upload and analyze identity documents for fraud detection.',
    endpoints: [
      {
        method: 'POST',
        path: '/api/analyze',
        description:
          'Analyze an uploaded document. Accepts multipart form data with file, applicant name, document type, and optional reference.',
      },
      {
        method: 'GET',
        path: '/api/analysis/{id}',
        description: 'Retrieve the full analysis result for a given case ID.',
      },
    ],
  },
  {
    title: 'KYC Cases',
    description: 'Manage Know Your Customer verification cases.',
    endpoints: [
      {
        method: 'GET',
        path: '/api/kyc/cases',
        description:
          'List all KYC cases with pagination, filtering, and statistics. Query params: page, page_size, status.',
      },
      {
        method: 'GET',
        path: '/api/kyc/cases/{id}',
        description: 'Get detailed information for a specific KYC case.',
      },
      {
        method: 'PATCH',
        path: '/api/kyc/cases/{id}',
        description:
          'Update a KYC case status or add notes. Body: { status, notes }.',
      },
      {
        method: 'DELETE',
        path: '/api/kyc/cases/{id}',
        description: 'Delete a KYC case and associated data.',
      },
    ],
  },
  {
    title: 'Clients',
    description: 'Manage client registrations and profiles.',
    endpoints: [
      {
        method: 'GET',
        path: '/api/clients',
        description: 'List all registered clients.',
      },
      {
        method: 'POST',
        path: '/api/clients',
        description:
          'Register a new client. Body: { name, email, webhook_url }.',
      },
      {
        method: 'GET',
        path: '/api/clients/{id}',
        description: 'Get client details.',
      },
      {
        method: 'DELETE',
        path: '/api/clients/{id}',
        description: 'Delete a client.',
      },
    ],
  },
  {
    title: 'Webhooks',
    description: 'Configure webhook notifications for analysis events.',
    endpoints: [
      {
        method: 'GET',
        path: '/api/webhooks',
        description: 'List all configured webhooks.',
      },
      {
        method: 'POST',
        path: '/api/webhooks',
        description:
          'Create a new webhook. Body: { url, events, secret }.',
      },
      {
        method: 'DELETE',
        path: '/api/webhooks/{id}',
        description: 'Delete a webhook.',
      },
    ],
  },
  {
    title: 'AML Screening',
    description: 'Anti-Money Laundering and sanctions screening.',
    endpoints: [
      {
        method: 'POST',
        path: '/api/screening/aml',
        description:
          'Screen an individual against AML databases and sanctions lists.',
      },
      {
        method: 'GET',
        path: '/api/screening/{id}',
        description: 'Get screening results for a given screening ID.',
      },
    ],
  },
  {
    title: 'Reports',
    description: 'Generate and retrieve analysis reports.',
    endpoints: [
      {
        method: 'GET',
        path: '/api/reports/{case_id}/pdf',
        description:
          'Download a PDF report for a specific case.',
      },
      {
        method: 'POST',
        path: '/api/reports/{case_id}/generate',
        description:
          'Generate a report for a case (async). Returns a job ID.',
      },
    ],
  },
  {
    title: 'Configuration',
    description: 'System configuration and rule management.',
    endpoints: [
      {
        method: 'GET',
        path: '/api/config/analysis-rules',
        description: 'Get the current analysis rules configuration.',
      },
      {
        method: 'PUT',
        path: '/api/config/analysis-rules',
        description: 'Update analysis rules configuration.',
      },
      {
        method: 'GET',
        path: '/api/config/system',
        description: 'Get system configuration (admin only).',
      },
      {
        method: 'GET',
        path: '/api/config/models',
        description: 'Get available AI model configurations.',
      },
    ],
  },
]

function MethodBadge({ method }: { method: string }) {
  const colors: Record<string, string> = {
    GET: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    POST: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    PUT: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    PATCH: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
    DELETE: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  }
  return (
    <Badge variant='secondary' className={`font-mono text-xs ${colors[method] || ''}`}>
      {method}
    </Badge>
  )
}

export function APIDocsPage() {
  return (
    <>
      <Header>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ProfileDropdown />
      </Header>

      <Main>
        <div className='mb-6'>
          <h1 className='text-2xl font-bold tracking-tight'>API Documentation</h1>
          <p className='text-muted-foreground'>
            Complete reference for the DeepGuard FastAPI backend. Base URL: <code className='rounded bg-muted px-1.5 py-0.5 text-sm'>/api</code>
          </p>
        </div>

        <div className='space-y-6'>
          {endpointGroups.map((group) => (
            <Card key={group.title}>
              <CardHeader>
                <CardTitle>{group.title}</CardTitle>
                <CardDescription>{group.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className='space-y-3'>
                  {group.endpoints.map((endpoint) => (
                    <div
                      key={`${endpoint.method}-${endpoint.path}`}
                      className='flex items-start gap-3 rounded-lg border p-3'
                    >
                      <MethodBadge method={endpoint.method} />
                      <div className='flex-1 min-w-0'>
                        <code className='text-sm font-mono font-medium break-all'>
                          {endpoint.path}
                        </code>
                        <p className='mt-1 text-sm text-muted-foreground'>
                          {endpoint.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </Main>
    </>
  )
}
