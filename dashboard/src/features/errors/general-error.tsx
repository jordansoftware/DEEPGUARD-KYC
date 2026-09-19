import { Button } from '@/components/ui/button'

export function GeneralError() {
  return (
    <div className='flex h-full flex-col items-center justify-center gap-4'>
      <h1 className='text-4xl font-bold'>Error</h1>
      <p className='text-muted-foreground'>Something went wrong</p>
      <Button onClick={() => window.location.reload()}>Retry</Button>
    </div>
  )
}
