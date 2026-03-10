import type { ChartContract } from '@/features/visualization/types'
import type { EChartsOption } from 'echarts'

export function contractToEChartsOption(contract: ChartContract): EChartsOption {
  switch (contract.chart_type) {
    case 'bar_error_letters':
      return barErrorLettersOption(contract)
    case 'boxplot':
      return boxplotOption(contract)
    case 'violin':
      return violinOption(contract)
    case 'scatter':
    case 'biplot':
      return scatterOption(contract)
    case 'heatmap':
      return heatmapOption(contract)
    default:
      return fallbackOption(contract)
  }
}

function barErrorLettersOption(c: ChartContract): EChartsOption {
  const series = c.series[0]
  const categories = c.x_axis?.data as string[] ?? []
  const means = series.data as number[]
  const errors = series.error_bars ?? []

  const letterAnnotations = c.annotations.filter((a) => a.type === 'letter')

  const option: EChartsOption = {
    title: { text: c.title, left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: categories, name: c.x_axis?.label },
    yAxis: { type: 'value', name: c.y_axis?.label },
    series: [
      {
        name: series.name,
        type: 'bar',
        data: means,
        itemStyle: { color: series.color ?? '#5470c6' },
      },
      ...(errors.length > 0
        ? [
            {
              type: 'custom' as const,
              name: 'Error Bars',
              renderItem: (_params: unknown, api: { value: (i: number) => number; coord: (v: number[]) => number[]; style: (opt: unknown) => unknown }) => {
                const idx = api.value(0) as number
                const mean = means[idx] ?? 0
                const sd = errors[idx] ?? 0
                const high = api.coord([idx, mean + sd])
                const low = api.coord([idx, mean - sd])
                return {
                  type: 'group',
                  children: [
                    { type: 'line', shape: { x1: high[0], y1: high[1], x2: low[0], y2: low[1] }, style: { stroke: '#333', lineWidth: 1.5 } },
                    { type: 'line', shape: { x1: high[0] - 5, y1: high[1], x2: high[0] + 5, y2: high[1] }, style: { stroke: '#333', lineWidth: 1.5 } },
                    { type: 'line', shape: { x1: low[0] - 5, y1: low[1], x2: low[0] + 5, y2: low[1] }, style: { stroke: '#333', lineWidth: 1.5 } },
                  ],
                }
              },
              encode: { x: 0 },
              data: categories.map((_, i) => [i]),
              z: 10,
            },
          ]
        : []),
    ],
    graphic: letterAnnotations.map((ann) => ({
      type: 'text',
      left: 'center',
      style: {
        text: ann.text ?? '',
        fontSize: 14,
        fontWeight: 'bold',
      },
      position: ann.position ? [ann.position.x * 100, ann.position.y] : [0, 0],
    })),
  }

  return option
}

function boxplotOption(c: ChartContract): EChartsOption {
  const series = c.series[0]
  const categories = c.x_axis?.data as string[] ?? []

  return {
    title: { text: c.title, left: 'center' },
    tooltip: { trigger: 'item' },
    xAxis: { type: 'category', data: categories, name: c.x_axis?.label },
    yAxis: { type: 'value', name: c.y_axis?.label },
    series: [
      {
        name: series.name,
        type: 'boxplot',
        data: series.data as number[][],
      },
    ],
  }
}

function violinOption(c: ChartContract): EChartsOption {
  const series = c.series[0]
  const categories = c.x_axis?.data as string[] ?? []

  return {
    title: { text: c.title, left: 'center' },
    tooltip: { trigger: 'item' },
    xAxis: { type: 'category', data: categories, name: c.x_axis?.label },
    yAxis: { type: 'value', name: c.y_axis?.label },
    series: [
      {
        name: series.name,
        type: 'boxplot',
        data: (series.data as number[][]).map((vals) => {
          if (vals.length === 0) return [0, 0, 0, 0, 0]
          const sorted = [...vals].sort((a, b) => a - b)
          const q1 = sorted[Math.floor(sorted.length * 0.25)]
          const median = sorted[Math.floor(sorted.length * 0.5)]
          const q3 = sorted[Math.floor(sorted.length * 0.75)]
          return [sorted[0], q1, median, q3, sorted[sorted.length - 1]]
        }),
      },
    ],
  }
}

function scatterOption(c: ChartContract): EChartsOption {
  return {
    title: { text: c.title, left: 'center' },
    tooltip: { trigger: 'item' },
    xAxis: { type: 'value', name: c.x_axis?.label },
    yAxis: { type: 'value', name: c.y_axis?.label },
    series: c.series.map((s) => ({
      name: s.name,
      type: 'scatter' as const,
      data: s.data,
      itemStyle: s.color ? { color: s.color } : undefined,
    })),
    legend: c.legend.length > 0 ? { data: c.legend } : undefined,
  }
}

function heatmapOption(c: ChartContract): EChartsOption {
  const series = c.series[0]
  return {
    title: { text: c.title, left: 'center' },
    tooltip: { trigger: 'item' },
    xAxis: { type: 'category', data: c.x_axis?.data as string[] },
    yAxis: { type: 'category', data: c.y_axis?.data as string[] },
    visualMap: { min: -1, max: 1, inRange: { color: ['#313695', '#f7f7f7', '#a50026'] } },
    series: [
      {
        name: series.name,
        type: 'heatmap',
        data: series.data,
      },
    ],
  }
}

function fallbackOption(c: ChartContract): EChartsOption {
  return {
    title: { text: c.title || 'Chart', left: 'center' },
    tooltip: {},
    xAxis: { type: 'category', data: c.x_axis?.data as string[] ?? [] },
    yAxis: { type: 'value' },
    series: c.series.map((s) => ({
      name: s.name,
      type: (s.type === 'bar' ? 'bar' : 'line') as 'bar' | 'line',
      data: s.data,
    })),
  }
}
