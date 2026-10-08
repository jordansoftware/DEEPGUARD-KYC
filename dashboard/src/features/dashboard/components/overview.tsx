import { useQuery } from '@tanstack/react-query'
import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { apiFetch } from '@/lib/api'

interface TrendData {
  date: string
  total: number
  approved: number
  rejected: number
  review: number
}

export function Overview() {
  const { data } = useQuery<{ trends: TrendData[] }>({
    queryKey: ['analytics-trends'],
    queryFn: async () => {
      return apiFetch('/analytics/trends?days=30')
    },
  })

  const chartData =
    data?.trends?.map((d) => ({
      name: d.date.slice(5),
      approved: d.approved,
      rejected: d.rejected,
      review: d.review,
      total: d.total,
    })) ?? []

  if (chartData.length === 0) {
    return (
      <div className='flex h-80 items-center justify-center text-sm text-muted-foreground'>
        No data available.
      </div>
    )
  }

  return (
    <ResponsiveContainer width='100%' height={300}>
      <BarChart data={chartData} barSize={4}>
        <CartesianGrid strokeDasharray='3 3' className='stroke-muted' />
        <XAxis
          dataKey='name'
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          interval={4}
        />
        <YAxis
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={30}
        />
        <Tooltip contentStyle={{ fontSize: 12 }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar
          dataKey='approved'
          stackId='a'
          fill='#22c55e'
          radius={[2, 2, 0, 0]}
        />
        <Bar dataKey='review' stackId='a' fill='#eab308' />
        <Bar
          dataKey='rejected'
          stackId='a'
          fill='#ef4444'
          radius={[0, 0, 2, 2]}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
