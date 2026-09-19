import { Link } from '@tanstack/react-router'
import { Menu, X } from 'lucide-react'
import {
  SidebarMenu,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar'
import { Button } from '../ui/button'

export function AppTitle() {
  const { toggleSidebar, setOpenMobile } = useSidebar()

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <div className='flex items-center justify-between gap-2 px-2 py-1.5'>
          <Link
            to='/'
            onClick={() => setOpenMobile(false)}
            className='grid flex-1 text-start text-sm leading-tight hover:bg-transparent'
          >
            <span className='truncate font-bold'>DeepGuard</span>
            <span className='truncate text-xs text-muted-foreground'>
              KYC Platform
            </span>
          </Link>
          <Button
            data-sidebar='trigger'
            data-slot='sidebar-trigger'
            variant='ghost'
            size='icon'
            className='aspect-square size-8 max-md:scale-125'
            onClick={toggleSidebar}
          >
            <X className='md:hidden' />
            <Menu className='max-md:hidden' />
            <span className='sr-only'>Toggle Sidebar</span>
          </Button>
        </div>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
