import { useMemo } from 'react'
import { GenericChart } from '@/components/GenericChart'
import { computeEllipse } from '@/utils/ellipseCalc'
import type { ChartContract } from '../types'

interface OrdinationScatterProps {
  contract: ChartContract
  height?: number
}

export function OrdinationScatter({ contract, height = 500 }: OrdinationScatterProps) {
  const option = useMemo(() => {
    const seriesList: Record<string, unknown>[] = []
    const legendData: string[] = []

    for (const s of contract.series) {
      legendData.push(s.name)
      seriesList.push({
        name: s.name,
        type: 'scatter',
        data: s.data,
        symbolSize: 8,
        itemStyle: s.color ? { color: s.color } : undefined,
      })

      const points = s.data as [number, number][]
      if (points.length >= 3) {
        const ellipsePoints = computeEllipse(points, 0.95)
        if (ellipsePoints.length > 0) {
          seriesList.push({
            name: `${s.name} (95% CI)`,
            type: 'line',
            data: ellipsePoints,
            smooth: true,
            showSymbol: false,
            lineStyle: { type: 'dashed', width: 1.5 },
            itemStyle: s.color ? { color: s.color } : undefined,
          })
        }
      }
    }

    return {
      title: { text: contract.title, left: 'center' },
      tooltip: { trigger: 'item' as const },
      legend: { data: legendData, bottom: 0 },
      xAxis: {
        type: 'value' as const,
        name: contract.x_axis?.label ?? 'Axis 1',
        nameLocation: 'center' as const,
        nameGap: 30,
      },
      yAxis: {
        type: 'value' as const,
        name: contract.y_axis?.label ?? 'Axis 2',
        nameLocation: 'center' as const,
        nameGap: 40,
      },
      series: seriesList,
    }
  }, [contract])

  return <GenericChart option={option} height={height} />
}
