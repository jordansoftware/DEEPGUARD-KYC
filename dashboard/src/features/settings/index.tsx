import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Key, User, Copy, Check, RefreshCw, Plus, Loader2 } from 'lucide-react'
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
import { ThemeSwitch } from '@/components/theme-switch'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { apiFetch } from '@/lib/api'

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

function getStoredKey(): string {
  return localStorage.getItem('deepguard_api_key') || ''
}

function storeKey(key: string) {
  if (key) {
    localStorage.setItem('deepguard_api_key', key)
  } else {
    localStorage.removeItem('deepguard_api_key')
  }
}

export function Settings() {
  const [apiKey, setApiKey] = useState(() => getStoredKey())
  const [saved, setSaved] = useState(false)
  const [copied, setCopied] = useState(false)
  const queryClient = useQueryClient()

  // Fetch current client's API key from the backend
  const { data: currentClient, isLoading: clientLoading, isError: clientError } =
    useQuery<Client>({
      queryKey: ['current-client'],
      queryFn: async () => {
        // Get the list of clients and return the first one (current user's)
        const clients = await apiFetch('/clients')
        return clients[0]
      },
      retry: false,
    })

  const handleSaveKey = () => {
    storeKey(apiKey.trim())
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleCopyKey = () => {
    if (!apiKey) return
    void navigator.clipboard.writeText(apiKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleUseClientKey = () => {
    if (currentClient?.api_key) {
      setApiKey(currentClient.api_key)
      storeKey(currentClient.api_key)
    }
  }

  const rotateMutation = useMutation({
    mutationFn: async () => {
      if (!currentClient) return null
      return apiFetch(`/clients/${currentClient.id}/rotate-key`, { method: 'POST' })
    },
    onSuccess: (data: { api_key: string }) => {
      if (data?.api_key) {
        setApiKey(data.api_key)
        storeKey(data.api_key)
        queryClient.invalidateQueries({ queryKey: ['current-client'] })
      }
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
          <h1 className='text-2xl font-bold tracking-tight'>Settings</h1>
          <p className='text-muted-foreground'>
            Manage your account settings and API key.
          </p>
        </div>

        <div className='space-y-6 max-w-2xl'>
          <Card>
            <CardHeader>
              <div className='flex items-center gap-3'>
                <div className='rounded-lg bg-primary/10 p-2'>
                  <User className='h-5 w-5 text-primary' />
                </div>
                <div>
                  <CardTitle>Profile</CardTitle>
                  <CardDescription>
                    {currentClient
                      ? `${currentClient.name} (${currentClient.email})`
                      : 'Your account information.'}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className='space-y-4'>
              {currentClient ? (
                <div className='space-y-2 text-sm'>
                  <div className='flex justify-between'>
                    <span className='text-muted-foreground'>Name</span>
                    <span>{currentClient.name}</span>
                  </div>
                  <div className='flex justify-between'>
                    <span className='text-muted-foreground'>Email</span>
                    <span>{currentClient.email}</span>
                  </div>
                  <div className='flex justify-between'>
                    <span className='text-muted-foreground'>Plan</span>
                    <Badge variant='secondary'>{currentClient.plan}</Badge>
                  </div>
                  <div className='flex justify-between'>
                    <span className='text-muted-foreground'>
                      Usage this month
                    </span>
                    <span>
                      {currentClient.used_this_month} / {currentClient.quota_monthly}
                    </span>
                  </div>
                </div>
              ) : (
                <p className='text-sm text-muted-foreground'>
                  No client found. Set an API key below.
                </p>
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
                  <CardTitle>API Key</CardTitle>
                  <CardDescription>
                    Set your API key for authenticated requests. Stored in
                    localStorage.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className='space-y-4'>
              <div className='grid gap-2'>
                <Label htmlFor='apikey'>API Key</Label>
                <div className='flex gap-2'>
                  <Input
                    id='apikey'
                    type='password'
                    placeholder='Enter your API key'
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                  />
                  <Button variant='outline' onClick={handleCopyKey} disabled={!apiKey}>
                    {copied ? (
                      <Check className='h-4 w-4' />
                    ) : (
                      <Copy className='h-4 w-4' />
                    )}
                  </Button>
                  <Button onClick={handleSaveKey}>
                    {saved ? 'Saved!' : 'Save'}
                  </Button>
                </div>
                <p className='text-xs text-muted-foreground'>
                  {apiKey ? 'API key is set and stored locally.' : 'No API key configured.'}
                </p>
              </div>

              {currentClient && (
                <div className='rounded-lg border p-3 space-y-3'>
                  <div className='text-sm font-medium'>
                    Link to your client account
                  </div>
                  <div className='flex flex-wrap gap-2'>
                    <Button
                      variant='outline'
                      size='sm'
                      onClick={handleUseClientKey}
                      disabled={clientLoading || !currentClient.api_key}
                    >
                      <Plus className='mr-1 h-3 w-3' />
                      Use my API key
                    </Button>
                    <Button
                      variant='outline'
                      size='sm'
                      onClick={() => rotateMutation.mutate()}
                      disabled={rotateMutation.isPending}
                    >
                      {rotateMutation.isPending ? (
                        <Loader2 className='mr-1 h-3 w-3 animate-spin' />
                      ) : (
                        <RefreshCw className='mr-1 h-3 w-3' />
                      )}
                      Rotate key
                    </Button>
                  </div>
                  {rotateMutation.data?.api_key && (
                    <div className='text-xs text-muted-foreground'>
                      New key generated (shown once). It is now stored in your
                      localStorage.
                    </div>
                  )}
                </div>
              )}

              {clientError && (
                <div className='text-xs text-destructive'>
                  Could not fetch your client account. Make sure the backend is
                  running and your current API key is valid.
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>
                Customize the look and feel of the application.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm font-medium'>Theme</p>
                  <p className='text-sm text-muted-foreground'>
                    Switch between light, dark, and system themes.
                  </p>
                </div>
                <ThemeSwitch />
              </div>
            </CardContent>
          </Card>
        </div>
      </Main>
    </>
  )
}
