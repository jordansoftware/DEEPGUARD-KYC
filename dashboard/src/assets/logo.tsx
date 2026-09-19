import { type SVGProps } from 'react'
import { cn } from '@/lib/utils'

export function Logo({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      id='deepguard-logo'
      viewBox='0 0 24 24'
      xmlns='http://www.w3.org/2000/svg'
      height='24'
      width='24'
      fill='none'
      stroke='currentColor'
      strokeWidth='2'
      strokeLinecap='round'
      strokeLinejoin='round'
      className={cn('size-6', className)}
      {...props}
    >
      <title>DeepGuard</title>
      <path d='M12 2L2 7v10l10 5 10-5V7L12 2z' />
      <path d='M12 22V12' />
      <path d='M12 12L2 7' />
      <path d='M12 12l10-5' />
    </svg>
  )
}
