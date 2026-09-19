import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Separator } from '@/components/ui/separator'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

function MethodBadge({ method }: { method: string }) {
  const colors: Record<string, string> = {
    GET: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    POST: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    GET_DETAIL: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  }
  return (
    <Badge
      variant='secondary'
      className={`font-mono text-xs ${colors[method] || ''}`}
    >
      {method}
    </Badge>
  )
}

function CodeBlock({
  children,
  language = 'bash',
}: {
  children: string
  language?: string
}) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    void navigator.clipboard.writeText(children)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className='relative my-3 rounded-lg border bg-muted/40'>
      <div className='flex items-center justify-between px-3 py-1.5 border-b'>
        <code className='text-xs font-mono text-muted-foreground'>
          {language}
        </code>
        <Button
          variant='ghost'
          size='sm'
          className='h-6 px-2'
          onClick={handleCopy}
        >
          {copied ? (
            <Check className='h-3 w-3' />
          ) : (
            <Copy className='h-3 w-3' />
          )}
        </Button>
      </div>
      <pre className='overflow-x-auto p-3 text-sm'>{children}</pre>
    </div>
  )
}

interface Step {
  title: string
  description: string
  code: string
}

const steps: Step[] = [
  {
    title: 'Clone & Run',
    description:
      'Spin up the full platform. Backend (API + AI engines) runs on :8765, the admin dashboard on :3000.',
    code: `git clone <repo-url> deepguard
cd deepguard
docker compose up -d
# Backend: http://localhost:8765
# Dashboard: http://localhost:3000`,
  },
  {
    title: 'Generate an API Key',
    description:
      'In the dashboard, go to Settings → API Keys. Or via API to create a new client (returns a fresh API key once):',
    code: `# Create a new client (returns a fresh API key once)
curl -X POST http://localhost:8765/api/clients \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: dg_demo" \\
  -d '{"name":"My App","email":"dev@myapp.com","plan":"pro"}'

# Response (api_key shown ONCE — store it securely):
# { "id": 2, "name": "My App", "api_key": "dg_a3xK9mP...", ... }`,
  },
  {
    title: 'Submit a KYC Document',
    description:
      'Send an ID document from your app. The forensic engine analyzes it (ELA, MELA, noise, metadata) and returns a verdict + score.',
    code: `curl -X POST http://localhost:8765/api/kyc/cases \\
  -H "X-API-Key: dg_a3xK9mP..." \\
  -F "file=@passport.jpg" \\
  -F "applicant=Jane Doe" \\
  -F "doc_type=cni" \\
  -F "reference=USER-0042"

# Response:
# { "id": 12, "verdict": "authentique", "score": 92, "status": "pending", ... }`,
  },
  {
    title: 'Receive the Verdict (Webhook)',
    description:
      'Configure a webhook to be notified when a case completes. The payload is HMAC-signed.',
    code: `curl -X POST http://localhost:8765/api/webhooks \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: dg_a3xK9mP..." \\
  -d '{"url":"https://myapp.com/hooks/kyccompleted","events":["case.completed"]}'

# Your endpoint receives (HMAC-signed with X-DeepGuard-Signature):
# { "event":"case.completed", "reference":"USER-0042", "verdict":"authentique", "score":92 }`,
  },
  {
    title: 'Verify Webhook Signature',
    description:
      'Validate the signature to ensure the payload is from DeepGuard and untampered.',
    code: `import hmac, hashlib

def verify(payload: bytes, signature: str, secret: str) -> bool:
    # payload = raw JSON body (bytes) received in the webhook POST
    # secret  = your DG_WEBHOOK_SECRET (set when creating the webhook)
    # signature = value of the X-DeepGuard-Signature header
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)`,
  },
]

const endpoints = [
  { method: 'POST', path: '/api/kyc/cases', description: 'Submit an ID document for KYC analysis' },
  { method: 'GET', path: '/api/kyc/cases/{id}', description: 'Get case detail (verdict, score, signals)' },
  { method: 'GET', path: '/api/kyc/cases', description: 'List cases (filter: status, q, page)' },
  { method: 'POST', path: '/api/kyc/cases/{id}/decision', description: 'Approve / reject / review a case' },
  { method: 'POST', path: '/api/analyze', description: 'Analyze an image (no case created)' },
  { method: 'POST', path: '/api/screening', description: 'AML / sanctions screening' },
  { method: 'POST', path: '/api/webhooks', description: 'Register a webhook' },
  { method: 'POST', path: '/api/clients', description: 'Create a new client (get API key)' },
  { method: 'GET', path: '/api/health', description: 'Health check' },
]

const responseFields = [
  {
    name: 'verdict',
    description: '"authentique" | "suspect" | "forge"',
  },
  {
    name: 'score',
    description: '0-100 (higher = more trustworthy)',
  },
  {
    name: 'status',
    description: '"pending" | "review" | "approved" | "rejected"',
  },
  {
    name: 'signals',
    description: 'Forensic sub-signals (mela, noise, ela, meta)',
  },
  {
    name: 'reasons',
    description: 'Human-readable audit trail',
  },
]

export function IntegrationPage() {
  return (
    <>
      <Header>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ProfileDropdown />
      </Header>

      <Main>
        <div className='mb-6'>
          <h1 className='text-2xl font-bold tracking-tight'>Integration Guide</h1>
          <p className='text-muted-foreground'>
            Connect your application to DeepGuard's KYC API.
          </p>
        </div>

        <div className='space-y-8'>
          {steps.map((step, index) => {
            const stepNumber = index + 1
            return (
              <div key={step.title} className='flex gap-4'>
                <div className='flex flex-col items-center'>
                  <div
                    className='flex h-7 w-7 items-center justify-center rounded-full border bg-primary text-primary-foreground text-xs font-bold'
                    aria-label={`Step ${stepNumber}`}
                  >
                    {stepNumber}
                  </div>
                  {stepNumber < steps.length && (
                    <div className='w-px flex-1 bg-border' />
                  )}
                </div>
                <div className='flex-1'>
                  <h2 className='text-lg font-semibold'>{step.title}</h2>
                  <p className='mt-1 text-sm text-muted-foreground'>
                    {step.description}
                  </p>
                  <CodeBlock
                    language={step === steps[4] ? 'python' : 'bash'}
                  >
                    {step.code}
                  </CodeBlock>
                </div>
              </div>
            )
          })}
        </div>

        <div className='mt-10 space-y-6'>
          <Card>
            <CardHeader>
              <CardTitle>Quick Reference</CardTitle>
              <CardDescription>
                All available backend endpoints. Base URL:{' '}
                <code className='rounded bg-muted px-1.5 py-0.5 text-sm'>
                  http://localhost:8765
                </code>
              </CardDescription>
            </CardHeader>
            <CardContent className='p-0'>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className='w-20'>Method</TableHead>
                    <TableHead className='font-mono'>Path</TableHead>
                    <TableHead>Description</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {endpoints.map((ep) => (
                    <TableRow key={`${ep.method}-${ep.path}`}>
                      <TableCell>
                        <MethodBadge method={ep.method} />
                      </TableCell>
                      <TableCell className='font-mono text-sm break-all'>
                        {ep.path}
                      </TableCell>
                      <TableCell className='text-sm'>
                        {ep.description}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Response Fields</CardTitle>
              <CardDescription>
                Key fields returned by KYC case endpoints.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className='space-y-4'>
                {responseFields.map((field, index) => (
                  <div key={field.name}>
                    {index > 0 && <Separator className='my-3' />}
                    <div className='flex items-start gap-3'>
                      <Badge
                        variant='outline'
                        className='font-mono text-xs mt-0.5'
                      >
                        {field.name}
                      </Badge>
                      <div className='text-sm text-muted-foreground'>
                        {field.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </Main>
    </>
  )
}
