import { Button } from '@/components/ui/button'

export function NotFoundError() {
  return (
    <div className='flex h-full flex-col items-center justify-center gap-4'>
      <h1 className='text-4xl font-bold'>404</h1>
      <p className='text-muted-foreground'>Page not found</p>
      <Button onClick={() => window.history.back()}>Go Back</Button>
    </div>
  )
}
