import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Key,
  Copy,
  Check,
  RefreshCw,
  Loader2,
  Trash2,
  AlertTriangle,
  Plus,
  Ban,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { apiFetch } from '@/lib/api'

const STORAGE_KEY = 'deepguard_api_key'

// A key's raw value is only returned once on create/rotate (security).
// We persist it here so the list can highlight the "Current" key.
function storedKeyFor(clientId: number): string {
  return localStorage.getItem(`${STORAGE_KEY}:key:${clientId}`) || ''
}

function rememberKeyFor(clientId: number, key: string) {
  localStorage.setItem(`${STORAGE_KEY}:key:${clientId}`, key)
}

const PLANS = ['free', 'starter', 'pro', 'enterprise'] as const
const EXPIRY_OPTIONS = [
  { value: 'none', label: 'No expiration' },
  { value: '30', label: '30 days' },
  { value: '90', label: '90 days' },
  { value: '365', label: '1 year' },
]

type Plan = (typeof PLANS)[number]
type Expiry = (typeof EXPIRY_OPTIONS)[number]['value']

interface Client {
  id: number
  name: string
  email: string
  api_key: string
  plan: string
  quota_monthly: number
  used_this_month: number
  active: boolean
  created_at: string
}

interface CreatedKey {
  key: string
  clientName: string
}

interface RotateResult {
  id: number
  api_key: string
  rotated_at: string
}

function storeKey(key: string) {
  if (key) {
    localStorage.setItem(STORAGE_KEY, key)
  } else {
    localStorage.removeItem(STORAGE_KEY)
  }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return iso
  }
}

function PlanBadge({ plan }: { plan: string }) {
  const variant =
    plan === 'enterprise'
      ? 'default'
      : plan === 'pro'
        ? 'destructive'
        : 'secondary'
  return <Badge variant={variant as 'default' | 'destructive' | 'secondary'}>{plan}</Badge>
}

export function ApiKeysPage() {
  const queryClient = useQueryClient()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [plan, setPlan] = useState<Plan>('free')
  const [expiry, setExpiry] = useState<Expiry>('none')
  const [createdKey, setCreatedKey] = useState<CreatedKey | null>(null)
  const [createdError, setCreatedError] = useState('')
  const [copied, setCopied] = useState(false)

  const [rotateResult, setRotateResult] = useState<{
    clientName: string
    key: string
  } | null>(null)
  const [rotateClientId, setRotateClientId] = useState<number | null>(null)
  const [revokeOpen, setRevokeOpen] = useState<number | null>(null)
  const [deleteOpen, setDeleteOpen] = useState<number | null>(null)

  const { data: clients, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['clients'],
    queryFn: () => apiFetch('/clients').then((r: unknown) => r as Client[]),
    retry: false,
  })

  const currentKey = localStorage.getItem(STORAGE_KEY)

  const createMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, string> = {
        name: name.trim(),
        email: email.trim() || 'dev@deepguard.local',
        plan,
      }
      const data = (await apiFetch('/clients', {
        method: 'POST',
        body: JSON.stringify(payload),
      })) as Client
      return { data, expiry }
    },
    onSuccess: ({ data, expiry: exp }) => {
      setCreatedKey({ key: data.api_key, clientName: data.name })
      storeKey(data.api_key)
      if (data.id) rememberKeyFor(data.id, data.api_key)
      setName('')
      setEmail('')
      setPlan('free')
      setExpiry(exp)
      setCreatedError('')
      void refetch()
    },
    onError: (err: Error) => {
      setCreatedError(err.message)
    },
  })

  const rotateMutation = useMutation({
    mutationFn: async (id: number) => {
      return (await apiFetch(`/clients/${id}/rotate-key`, {
        method: 'POST',
      })) as RotateResult
    },
    onSuccess: (data, id) => {
      const client = clients?.find((c: Client) => c.id === id)
      setRotateResult({ clientName: client?.name || `Key #${id}`, key: data.api_key })
      setRotateClientId(id)
      storeKey(data.api_key)
      rememberKeyFor(id, data.api_key)
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })

  const revokeMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiFetch(`/clients/${id}`, { method: 'DELETE' })
    },
    onSuccess: () => {
      setRevokeOpen(null)
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })

  const setAsCurrent = (key: string) => {
    storeKey(key)
    queryClient.invalidateQueries({ queryKey: ['clients'] })
  }

  const copyKey = (key: string) => {
    void navigator.clipboard.writeText(key)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleCreate = () => {
    setCreatedError('')
    createMutation.mutate()
  }

  const handleRotate = (id: number) => {
    rotateMutation.mutate(id)
  }

  const handleRevoke = (id: number) => {
    revokeMutation.mutate(id)
  }

  const handleDelete = (id: number) => {
    setDeleteOpen(id)
  }

  const handleDeleteConfirm = () => {
    if (deleteOpen !== null) {
      void (async () => {
        await apiFetch(`/clients/${deleteOpen}`, { method: 'DELETE' })
        setDeleteOpen(null)
        queryClient.invalidateQueries({ queryKey: ['clients'] })
      })()
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
          <h1 className='text-2xl font-bold tracking-tight'>API Keys</h1>
          <p className='text-muted-foreground'>
            Manage your DeepGuard API keys and access credentials.
          </p>
        </div>

        <div className='space-y-6 max-w-3xl'>
          <Card>
            <CardHeader>
              <div className='flex items-center gap-3'>
                <div className='rounded-lg bg-primary/10 p-2'>
                  <Plus className='h-5 w-5 text-primary' />
                </div>
                <div>
                  <CardTitle>Create a New API Key</CardTitle>
                  <CardDescription>
                    Generate a new API key for a specific use case.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className='space-y-4'>
              {createdKey ? (
                <div className='space-y-3'>
                  <div className='rounded-lg border bg-primary/5 p-4 space-y-2'>
                    <div className='text-sm font-medium'>
                      New API key created for{' '}
                      <span className='font-semibold'>{createdKey.clientName}</span>
                    </div>
                    <div className='flex items-center gap-2'>
                      <code className='flex-1 overflow-x-auto rounded bg-muted px-3 py-2 text-xs font-mono'>
                        {createdKey.key}
                      </code>
                      <Button
                        variant='outline'
                        size='sm'
                        onClick={() => copyKey(createdKey.key)}
                      >
                        {copied ? (
                          <Check className='h-4 w-4' />
                        ) : (
                          <Copy className='h-4 w-4' />
                        )}
                      </Button>
                    </div>
                    <div className='flex items-start gap-2 text-xs text-amber-600 dark:text-amber-400'>
                      <AlertTriangle className='mt-0.5 h-3.5 w-3.5 shrink-0' />
                      <span>
                        This key will not be shown again. Store it securely. It has
                        been saved to localStorage.
                      </span>
                    </div>
                  </div>
                  <Button
                    variant='outline'
                    size='sm'
                    onClick={() => setCreatedKey(null)}
                  >
                    Create another key
                  </Button>
                </div>
              ) : (
                <div className='space-y-4'>
                  <div className='grid gap-2'>
                    <Label htmlFor='key-name'>Name *</Label>
                    <Input
                      id='key-name'
                      placeholder='Production, Dev, CI'
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </div>

                  <div className='grid gap-2'>
                    <Label htmlFor='key-email'>Email</Label>
                    <Input
                      id='key-email'
                      placeholder='dev@deepguard.local'
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                    <p className='text-xs text-muted-foreground'>
                      Optional. Defaults to dev@deepguard.local
                    </p>
                  </div>

                  <div className='grid gap-2'>
                    <Label>Plan</Label>
                    <Select value={plan} onValueChange={(v) => setPlan(v as Plan)}>
                      <SelectTrigger className='w-full'>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PLANS.map((p) => (
                          <SelectItem key={p} value={p}>
                            {p}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className='grid gap-2'>
                    <Label>Expiration</Label>
                    <Select
                      value={expiry}
                      onValueChange={(v) => setExpiry(v as Expiry)}
                    >
                      <SelectTrigger className='w-full'>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {EXPIRY_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {expiry !== 'none' && (
                      <p className='text-xs text-muted-foreground'>
                        Expiry not enforced by backend yet. This is a client-side
                        reminder only.
                      </p>
                    )}
                  </div>

                  <div className='flex items-start gap-2 rounded-md bg-muted/50 p-3 text-xs text-muted-foreground'>
                    <AlertTriangle className='mt-0.5 h-3.5 w-3.5 shrink-0' />
                    <span>
                      The API key is shown once after creation. You must store it
                      securely.
                    </span>
                  </div>

                  {createdError && (
                    <div className='flex items-center gap-2 text-sm text-destructive'>
                      <AlertTriangle className='h-4 w-4' />
                      {createdError}
                    </div>
                  )}

                  <Button
                    onClick={handleCreate}
                    disabled={!name.trim() || createMutation.isPending}
                  >
                    {createMutation.isPending ? (
                      <>
                        <Loader2 className='mr-2 h-4 w-4 animate-spin' />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Plus className='mr-2 h-4 w-4' />
                        Create Key
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className='flex items-center gap-3'>
                <div className='rounded-lg bg-primary/10 p-2'>
                  <Key className='h-5 w-5 text-primary' />
                </div>
                <div>
                  <CardTitle>Your API Keys</CardTitle>
                  <CardDescription>
                    All keys associated with your DeepGuard account.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {rotateResult && (
                <div className='mb-4 rounded-lg border bg-primary/5 p-4 space-y-2'>
                  <div className='text-sm font-medium'>
                    Key rotated for <span className='font-semibold'>{rotateResult.clientName}</span>
                  </div>
                  <div className='flex items-center gap-2'>
                    <code className='flex-1 overflow-x-auto rounded bg-muted px-3 py-2 text-xs font-mono'>
                      {rotateResult.key}
                    </code>
                    <Button
                      variant='outline'
                      size='sm'
                      onClick={() => copyKey(rotateResult.key)}
                    >
                      {copied ? (
                        <Check className='h-4 w-4' />
                      ) : (
                        <Copy className='h-4 w-4' />
                      )}
                    </Button>
                  </div>
                  <div className='flex items-start gap-2 text-xs text-amber-600 dark:text-amber-400'>
                    <AlertTriangle className='mt-0.5 h-3.5 w-3.5 shrink-0' />
                    <span>
                      The old key is now invalid. This new key will not be shown
                      again. It has been saved to localStorage.
                    </span>
                  </div>
                  <Button
                    variant='outline'
                    size='sm'
                    onClick={() => {
                      setRotateResult(null)
                      setRotateClientId(null)
                    }}
                  >
                    Dismiss
                  </Button>
                </div>
              )}

              {isLoading ? (
                <div className='space-y-3'>
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className='h-12 w-full' />
                  ))}
                </div>
              ) : isError ? (
                <div className='flex flex-col items-center gap-3 py-8 text-center'>
                  <AlertTriangle className='h-8 w-8 text-destructive' />
                  <p className='text-sm text-muted-foreground'>
                    Could not load API keys. Make sure the backend is running.
                  </p>
                  <Button variant='outline' size='sm' onClick={() => refetch()} disabled={isFetching}>
                    <RefreshCw className={isFetching ? 'mr-2 h-4 w-4 animate-spin' : 'mr-2 h-4 w-4'} />
                    Retry
                  </Button>
                </div>
              ) : !clients || clients.length === 0 ? (
                <div className='flex flex-col items-center gap-2 py-8 text-center'>
                  <Key className='h-8 w-8 text-muted-foreground' />
                  <p className='text-sm text-muted-foreground'>
                    No API keys yet. Create your first key above.
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Plan</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className='text-right'>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {clients.map((client) => {
                      const keyValue =
                        client.api_key || storedKeyFor(client.id)
                      const isCurrent = !!keyValue && keyValue === currentKey
                      const isActive = client.active
                      return (
                        <TableRow
                          key={client.id}
                          className={isCurrent ? 'bg-primary/5' : ''}
                        >
                          <TableCell className='font-medium'>
                            <div className='flex items-center gap-2'>
                              <span>{client.name}</span>
                              {isCurrent && <Badge variant='default'>Current</Badge>}
                            </div>
                          </TableCell>
                          <TableCell>
                            <PlanBadge plan={client.plan} />
                          </TableCell>
                          <TableCell className='text-muted-foreground'>
                            {formatDate(client.created_at)}
                          </TableCell>
                          <TableCell>
                            {isActive ? (
                              <Badge variant='secondary'>active</Badge>
                            ) : (
                              <Badge variant='destructive'>inactive</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <div className='flex items-center justify-end gap-1.5'>
                              {isActive && !isCurrent && (
                                <Button
                                  variant='ghost'
                                  size='sm'
                                  className='h-7 text-xs'
                                  onClick={() => setAsCurrent(keyValue)}
                                  disabled={!keyValue}
                                >
                                  Set as Current
                                </Button>
                              )}
                              {isActive && (
                                <Button
                                  variant='ghost'
                                  size='sm'
                                  className='h-7 text-xs'
                                  onClick={() => handleRotate(client.id)}
                                  disabled={
                                    rotateMutation.isPending &&
                                    rotateClientId === client.id
                                  }
                                >
                                  {rotateMutation.isPending &&
                                  rotateClientId === client.id ? (
                                    <Loader2 className='mr-1 h-3 w-3 animate-spin' />
                                  ) : (
                                    <RefreshCw className='mr-1 h-3 w-3' />
                                  )}
                                  Rotate
                                </Button>
                              )}
                              {isActive && (
                                <Button
                                  variant='ghost'
                                  size='sm'
                                  className='h-7 text-xs text-destructive hover:text-destructive'
                                  onClick={() => setRevokeOpen(client.id)}
                                  disabled={revokeMutation.isPending}
                                >
                                  <Ban className='mr-1 h-3 w-3' />
                                  Revoke
                                </Button>
                              )}
                              {!isActive && (
                                <Button
                                  variant='ghost'
                                  size='sm'
                                  className='h-7 text-xs text-destructive hover:text-destructive'
                                  onClick={() => handleDelete(client.id)}
                                >
                                  <Trash2 className='mr-1 h-3 w-3' />
                                  Delete
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              )}

              {clients && clients.length > 0 && (
                <p className='mt-3 text-xs text-muted-foreground'>
                  Inactive keys can be deleted but cannot be reactivated.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </Main>

      <AlertDialog open={revokeOpen !== null} onOpenChange={(open) => !open && setRevokeOpen(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revoke API key?</AlertDialogTitle>
            <AlertDialogDescription>
              This will immediately deactivate the API key. Any requests using
              this key will be rejected. This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setRevokeOpen(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.stopPropagation()
                if (revokeOpen !== null) {
                  handleRevoke(revokeOpen)
                }
              }}
              disabled={revokeMutation.isPending}
              className='bg-destructive text-destructive-foreground'
            >
              {revokeMutation.isPending ? (
                <Loader2 className='mr-2 h-4 w-4 animate-spin' />
              ) : null}
              Revoke
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={deleteOpen !== null} onOpenChange={(open) => !open && setDeleteOpen(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete API key permanently?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove the key from your account. Inactive keys cannot
              be reactivated. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDeleteOpen(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.stopPropagation()
                handleDeleteConfirm()
              }}
              className='bg-destructive text-destructive-foreground'
            >
              <Trash2 className='mr-2 h-4 w-4' />
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
