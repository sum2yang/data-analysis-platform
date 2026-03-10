import { GenericChart } from '@/components/GenericChart'
import type { ChartContract } from '../types'

interface HeatmapChartProps {
  contract: ChartContract
  height?: number
}

export function HeatmapChart({ contract, height = 500 }: HeatmapChartProps) {
  const series = contract.series[0]
  const xLabels = (contract.x_axis?.data ?? []) as string[]
  const yLabels = (contract.y_axis?.data ?? []) as string[]

  const option = {
    title: { text: contract.title, left: 'center' },
    tooltip: {
      trigger: 'item' as const,
      formatter: (params: { value: [number, number, number] }) => {
        const [x, y, val] = params.value
        return `${xLabels[x]} vs ${yLabels[y]}: ${typeof val === 'number' ? val.toFixed(3) : val}`
      },
    },
    grid: { left: 120, bottom: 80, right: 60, top: 60 },
    xAxis: {
      type: 'category' as const,
      data: xLabels,
      axisLabel: { rotate: 45 },
    },
    yAxis: {
      type: 'category' as const,
      data: yLabels,
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: 'horizontal' as const,
      left: 'center',
      bottom: 0,
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#f7f7f7', '#fdae61', '#f46d43', '#d73027', '#a50026'],
      },
    },
    series: [
      {
        name: series?.name ?? 'Correlation',
        type: 'heatmap' as const,
        data: series?.data ?? [],
        label: {
          show: xLabels.length <= 10,
          formatter: (params: { value: [number, number, number] }) =>
            typeof params.value[2] === 'number' ? params.value[2].toFixed(2) : '',
        },
      },
    ],
  }

  return <GenericChart option={option} height={height} />
}
