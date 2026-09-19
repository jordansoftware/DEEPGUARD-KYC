import { useQuery } from '@tanstack/react-query'
import {
  Plug,
  CheckCircle2,
  XCircle,
  Send,
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
import { apiFetch } from '@/lib/api'

interface Plugin {
  name: string
  display_name: string
  description: string
  config_fields: string[]
  enabled: boolean
  config: Record<string, string>
}

export function PluginsPage() {
  const { data, isLoading, isError, refetch } = useQuery<{ plugins: Plugin[] }>({
    queryKey: ['plugins'],
    queryFn: async () => {
      return apiFetch('/plugins/')
    },
  })

  const togglePlugin = async (name: string, enabled: boolean) => {
    await apiFetch(`/plugins/${name}`, {
      method: 'PUT',
      body: JSON.stringify({ enabled }),
    })
    refetch()
  }

  const testPlugin = async (name: string) => {
    await apiFetch(`/plugins/${name}/test`, { method: 'POST' })
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
          <h1 className='text-2xl font-bold tracking-tight'>Integrations</h1>
          <p className='text-muted-foreground'>
            Connect DeepGuard with external services for notifications and automation.
          </p>
        </div>

        {isLoading ? (
          <div className='grid gap-4 md:grid-cols-2'>
            {Array.from({ length: 4 }).map((_, i) => (
              <Card key={i}>
                <CardContent className='p-6'>
                  <div className='h-20 animate-pulse rounded bg-muted' />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className='grid gap-4 md:grid-cols-2'>
            {data?.plugins?.map((plugin) => (
              <Card key={plugin.name}>
                <CardHeader>
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center gap-2'>
                      <Plug className='h-5 w-5 text-muted-foreground' />
                      <CardTitle className='text-lg'>{plugin.display_name}</CardTitle>
                    </div>
                    <Badge variant={plugin.enabled ? 'default' : 'secondary'}>
                      {plugin.enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <CardDescription>{plugin.description}</CardDescription>
                </CardHeader>
                <CardContent className='space-y-4'>
                  {plugin.enabled && plugin.config_fields.length > 0 && (
                    <div className='space-y-2'>
                      {plugin.config_fields.map((field) => (
                        <div key={field}>
                          <label className='text-xs font-medium text-muted-foreground capitalize'>
                            {field.replace(/_/g, ' ')}
                          </label>
                          <input
                            type='text'
                            placeholder={`Enter ${field.replace(/_/g, ' ')}`}
                            className='mt-1 flex h-8 w-full rounded-md border border-input bg-background px-2 text-sm'
                          />
                        </div>
                      ))}
                    </div>
                  )}
                  <div className='flex gap-2'>
                    <Button
                      variant={plugin.enabled ? 'outline' : 'default'}
                      size='sm'
                      onClick={() => togglePlugin(plugin.name, !plugin.enabled)}
                    >
                      {plugin.enabled ? (
                        <><XCircle className='mr-1 h-3 w-3' /> Disable</>
        ) : isError ? (
          <div className='rounded-md border p-6 text-center text-sm text-muted-foreground'>
            Failed to load plugins. Please check your API key settings.
          </div>
        ) : (
                        <><CheckCircle2 className='mr-1 h-3 w-3' /> Enable</>
                      )}
                    </Button>
                    {plugin.enabled && (
                      <Button variant='ghost' size='sm' onClick={() => testPlugin(plugin.name)}>
                        <Send className='mr-1 h-3 w-3' /> Test
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </Main>
    </>
  )
}
