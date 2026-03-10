import { useMemo } from 'react'
import { GenericChart } from '@/components/GenericChart'
import { computeEllipse } from '@/utils/ellipseCalc'
import type { ChartContract } from '../types'

interface RdaBiplotProps {
  contract: ChartContract
  height?: number
}

export function RdaBiplot({ contract, height = 550 }: RdaBiplotProps) {
  const option = useMemo(() => {
    const seriesList: Record<string, unknown>[] = []
    const legendData: string[] = []

    for (const s of contract.series) {
      if (s.type === 'scatter') {
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
          const ellipse = computeEllipse(points, 0.95)
          if (ellipse.length > 0) {
            seriesList.push({
              name: `${s.name} (95%)`,
              type: 'line',
              data: ellipse,
              smooth: true,
              showSymbol: false,
              lineStyle: { type: 'dashed', width: 1 },
              itemStyle: s.color ? { color: s.color } : undefined,
            })
          }
        }
      }
    }

    const arrows = contract.annotations.filter((a) => a.type === 'line')
    const arrowGraphics = arrows.map((arrow) => {
      const pos = arrow.position ?? { x: 0, y: 0 }
      return {
        type: 'line' as const,
        shape: {
          x1: 0, y1: 0,
          x2: pos.x * 100,
          y2: pos.y * 100,
        },
        style: {
          stroke: '#d73027',
          lineWidth: 2,
        },
      }
    })

    const arrowLabels = arrows.map((arrow) => {
      const pos = arrow.position ?? { x: 0, y: 0 }
      return {
        type: 'text' as const,
        style: {
          text: arrow.text ?? '',
          x: pos.x * 105,
          y: pos.y * 105,
          fontSize: 11,
          fill: '#d73027',
        },
      }
    })

    return {
      title: { text: contract.title, left: 'center' },
      tooltip: { trigger: 'item' as const },
      legend: { data: legendData, bottom: 0 },
      xAxis: {
        type: 'value' as const,
        name: contract.x_axis?.label ?? 'Axis 1',
        nameLocation: 'center' as const,
        nameGap: 30,
        axisLine: { onZero: true },
      },
      yAxis: {
        type: 'value' as const,
        name: contract.y_axis?.label ?? 'Axis 2',
        nameLocation: 'center' as const,
        nameGap: 40,
        axisLine: { onZero: true },
      },
      series: seriesList,
      graphic: [...arrowGraphics, ...arrowLabels],
    }
  }, [contract])

  return <GenericChart option={option} height={height} />
}
