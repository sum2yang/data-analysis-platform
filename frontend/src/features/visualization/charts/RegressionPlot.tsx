import { useMemo } from 'react'
import { GenericChart } from '@/components/GenericChart'
import type { ChartContract } from '../types'

interface RegressionPlotProps {
  contract: ChartContract
  height?: number
}

export function RegressionPlot({ contract, height = 400 }: RegressionPlotProps) {
  const option = useMemo(() => {
    const seriesList: Record<string, unknown>[] = []

    for (const s of contract.series) {
      if (s.type === 'scatter') {
        seriesList.push({
          name: s.name,
          type: 'scatter',
          data: s.data,
          symbolSize: 6,
        })
      } else if (s.type === 'line') {
        seriesList.push({
          name: s.name,
          type: 'line',
          data: s.data,
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2 },
        })
      }
    }

    return {
      title: { text: contract.title, left: 'center' },
      tooltip: { trigger: 'item' as const },
      legend: { bottom: 0 },
      xAxis: {
        type: 'value' as const,
        name: contract.x_axis?.label ?? 'X',
        nameLocation: 'center' as const,
        nameGap: 30,
      },
      yAxis: {
        type: 'value' as const,
        name: contract.y_axis?.label ?? 'Y',
        nameLocation: 'center' as const,
        nameGap: 40,
      },
      series: seriesList,
    }
  }, [contract])

  return <GenericChart option={option} height={height} />
}
