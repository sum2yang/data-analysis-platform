import type { ChartContract } from '@/features/visualization/types'
import type { EChartsOption } from 'echarts'

const GROUP_COLORS = [
  '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
  '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b8d0',
]

export function contractToEChartsOption(contract: ChartContract): EChartsOption {
  switch (contract.chart_type) {
    case 'bar_error_letters':
      return barErrorLettersOption(contract)
    case 'boxplot':
      return boxplotOption(contract)
    case 'violin':
      return violinOption(contract)
    case 'ordination_scatter':
    case 'scatter':
      return ordinationScatterOption(contract)
    case 'rda_biplot':
    case 'biplot':
      return rdaBiplotOption(contract)
    case 'heatmap':
      return heatmapOption(contract)
    case 'regression_plot':
      return regressionPlotOption(contract)
    default:
      return fallbackOption(contract)
  }
}

/* ------------------------------------------------------------------ */
/*  Bar + Error Bars + Significance Letters                           */
/* ------------------------------------------------------------------ */

function barErrorLettersOption(c: ChartContract): EChartsOption {
  const series = c.series[0]
  const categories = c.x_axis?.data as string[] ?? []
  const means = series.data as number[]
  const errors = series.error_bars ?? []

  const letterAnnotations = c.annotations.filter((a) => a.type === 'letter')

  // Build markPoint data for significance letters above bars
  const markPointData = letterAnnotations.map((ann) => {
    const pos = ann.position as { x: number; y: number } | undefined
    const catIdx = pos?.x ?? 0
    const yVal = pos?.y ?? 0
    return {
      coord: [catIdx, yVal],
      value: ann.text ?? '',
      symbol: 'none',
      label: {
        show: true,
        formatter: ann.text ?? '',
        fontSize: 14,
        fontWeight: 'bold' as const,
        color: '#333',
        offset: [0, -8],
      },
    }
  })

  const option: EChartsOption = {
    title: { text: c.title, left: 'center' },
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
        const p = (Array.isArray(params) ? params[0] : params) as { name: string; value: number; dataIndex: number }
        const idx = p.dataIndex
        const mean = means[idx] ?? 0
        const sd = errors[idx] ?? 0
        return `<b>${p.name}</b><br/>Mean: ${mean.toFixed(3)}<br/>SD: ${sd.toFixed(3)}`
      },
    },
    grid: { top: 60, bottom: 40, left: 60, right: 20 },
    xAxis: { type: 'category', data: categories, name: c.x_axis?.label },
    yAxis: { type: 'value', name: c.y_axis?.label },
    series: [
      {
        name: series.name,
        type: 'bar',
        data: means,
        itemStyle: { color: series.color ?? '#5470c6' },
        barMaxWidth: 60,
        markPoint: markPointData.length > 0 ? { data: markPointData } : undefined,
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
                const capW = 5
                return {
                  type: 'group',
                  children: [
                    { type: 'line', shape: { x1: high[0], y1: high[1], x2: low[0], y2: low[1] }, style: { stroke: '#333', lineWidth: 1.5 } },
                    { type: 'line', shape: { x1: high[0] - capW, y1: high[1], x2: high[0] + capW, y2: high[1] }, style: { stroke: '#333', lineWidth: 1.5 } },
                    { type: 'line', shape: { x1: low[0] - capW, y1: low[1], x2: low[0] + capW, y2: low[1] }, style: { stroke: '#333', lineWidth: 1.5 } },
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
  }

  return option
}

/* ------------------------------------------------------------------ */
/*  Boxplot                                                           */
/* ------------------------------------------------------------------ */

function boxplotOption(c: ChartContract): EChartsOption {
  const series = c.series[0]
  const categories = c.x_axis?.data as string[] ?? []

  return {
    title: { text: c.title, left: 'center' },
    tooltip: { trigger: 'item' },
    grid: { top: 60, bottom: 40, left: 60, right: 20 },
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

/* ------------------------------------------------------------------ */
/*  Violin (boxplot + jitter scatter overlay)                         */
/* ------------------------------------------------------------------ */

function violinOption(c: ChartContract): EChartsOption {
  const series = c.series[0]
  const categories = c.x_axis?.data as string[] ?? []
  const rawGroups = series.data as number[][]

  // Compute boxplot summaries from raw values
  const boxData = rawGroups.map((vals) => {
    if (!vals || vals.length === 0) return [0, 0, 0, 0, 0]
    const sorted = [...vals].sort((a, b) => a - b)
    const q1 = sorted[Math.floor(sorted.length * 0.25)]
    const median = sorted[Math.floor(sorted.length * 0.5)]
    const q3 = sorted[Math.floor(sorted.length * 0.75)]
    return [sorted[0], q1, median, q3, sorted[sorted.length - 1]]
  })

  // Build jitter scatter data: [[catIndex + jitter, value], ...]
  const jitterData: [number, number][] = []
  rawGroups.forEach((vals, catIdx) => {
    if (!vals) return
    for (const v of vals) {
      const jitter = (Math.random() - 0.5) * 0.3
      jitterData.push([catIdx + jitter, v])
    }
  })

  return {
    title: { text: c.title, left: 'center' },
    tooltip: { trigger: 'item' },
    grid: { top: 60, bottom: 40, left: 60, right: 20 },
    xAxis: { type: 'category', data: categories, name: c.x_axis?.label },
    yAxis: { type: 'value', name: c.y_axis?.label },
    series: [
      {
        name: series.name,
        type: 'boxplot',
        data: boxData,
      },
      {
        name: 'Data Points',
        type: 'scatter',
        data: jitterData,
        symbolSize: 4,
        itemStyle: { color: 'rgba(100, 100, 100, 0.4)' },
        z: 5,
      },
    ],
  }
}

/* ------------------------------------------------------------------ */
/*  Ordination Scatter (PCA/PCoA/NMDS) with optional ellipses         */
/* ------------------------------------------------------------------ */

function ordinationScatterOption(c: ChartContract): EChartsOption {
  const ellipses = c.metadata?.ellipses as Array<{
    group: string
    points: Array<{ x: number; y: number }>
  }> | undefined

  const scatterSeries = c.series.map((s, idx) => ({
    name: s.name,
    type: 'scatter' as const,
    data: s.data,
    symbolSize: 8,
    itemStyle: { color: s.color ?? GROUP_COLORS[idx % GROUP_COLORS.length] },
  }))

  // Render ellipses as custom polygon series
  const ellipseSeries = (ellipses ?? []).map((ell, eIdx) => {
    // Find matching group color
    const groupIdx = c.series.findIndex((s) => s.name === ell.group)
    const color = groupIdx >= 0
      ? (c.series[groupIdx].color ?? GROUP_COLORS[groupIdx % GROUP_COLORS.length])
      : GROUP_COLORS[eIdx % GROUP_COLORS.length]

    const pts = ell.points.map((p) => [p.x, p.y])

    return {
      type: 'custom' as const,
      name: `${ell.group} (95% CI)`,
      renderItem: (_params: unknown, api: { coord: (v: number[]) => number[] }) => {
        const pixelPts = pts.map((p) => api.coord(p))
        return {
          type: 'polygon',
          shape: { points: pixelPts },
          style: {
            fill: color,
            opacity: 0.15,
            stroke: color,
            lineWidth: 1.5,
          },
        }
      },
      data: [{ value: [0] }],
      z: 1,
    }
  })

  return {
    title: { text: c.title, left: 'center' },
    tooltip: {
      trigger: 'item',
      formatter: (params: unknown) => {
        const p = params as { seriesName: string; value: number[] }
        if (p.value && p.value.length >= 2) {
          return `<b>${p.seriesName}</b><br/>X: ${p.value[0].toFixed(3)}<br/>Y: ${p.value[1].toFixed(3)}`
        }
        return ''
      },
    },
    grid: { top: 60, bottom: 40, left: 70, right: 20 },
    xAxis: { type: 'value', name: c.x_axis?.label, nameLocation: 'center', nameGap: 28 },
    yAxis: { type: 'value', name: c.y_axis?.label, nameLocation: 'center', nameGap: 50 },
    legend: c.legend.length > 0 ? { data: c.legend, top: 28 } : undefined,
    series: [...scatterSeries, ...ellipseSeries],
  }
}

/* ------------------------------------------------------------------ */
/*  RDA/CCA Biplot with arrows                                        */
/* ------------------------------------------------------------------ */

function rdaBiplotOption(c: ChartContract): EChartsOption {
  const arrowAnnotations = c.annotations.filter((a) => a.type === 'arrow')

  const scatterSeries = c.series.map((s, idx) => ({
    name: s.name,
    type: 'scatter' as const,
    data: s.data,
    symbolSize: 8,
    itemStyle: { color: s.color ?? GROUP_COLORS[idx % GROUP_COLORS.length] },
  }))

  // Build arrow markLines on a dummy series
  const arrowMarkLines = arrowAnnotations.map((ann) => {
    const pos = ann.position as { from: { x: number; y: number }; to: { x: number; y: number } } | undefined
    if (!pos) return null
    return {
      symbol: ['none', 'arrow'],
      symbolSize: 8,
      lineStyle: { color: '#d14', width: 1.5 },
      label: {
        show: true,
        formatter: ann.text ?? '',
        position: 'end' as const,
        fontSize: 11,
        color: '#333',
      },
      data: [
        [
          { coord: [pos.from.x, pos.from.y] },
          { coord: [pos.to.x, pos.to.y] },
        ],
      ],
    }
  }).filter(Boolean)

  // Add a hidden scatter series to carry markLines for biplot arrows
  const arrowSeries = arrowMarkLines.length > 0
    ? [{
        type: 'scatter' as const,
        name: 'Environmental Variables',
        data: [] as unknown[],
        markLine: {
          silent: true,
          animation: false,
          data: arrowMarkLines.map((ml) => ml!.data[0]),
          symbol: ['none', 'arrow'],
          symbolSize: 8,
          lineStyle: { color: '#d14', width: 1.5 },
          label: { show: true, position: 'end' as const, fontSize: 11, color: '#333' },
        },
      }]
    : []

  // Render ellipses if present
  const ellipses = c.metadata?.ellipses as Array<{
    group: string
    points: Array<{ x: number; y: number }>
  }> | undefined

  const ellipseSeries = (ellipses ?? []).map((ell, eIdx) => {
    const groupIdx = c.series.findIndex((s) => s.name === ell.group)
    const color = groupIdx >= 0
      ? (c.series[groupIdx].color ?? GROUP_COLORS[groupIdx % GROUP_COLORS.length])
      : GROUP_COLORS[eIdx % GROUP_COLORS.length]
    const pts = ell.points.map((p) => [p.x, p.y])

    return {
      type: 'custom' as const,
      name: `${ell.group} (95% CI)`,
      renderItem: (_params: unknown, api: { coord: (v: number[]) => number[] }) => {
        const pixelPts = pts.map((p) => api.coord(p))
        return {
          type: 'polygon',
          shape: { points: pixelPts },
          style: { fill: color, opacity: 0.15, stroke: color, lineWidth: 1.5 },
        }
      },
      data: [{ value: [0] }],
      z: 1,
    }
  })

  return {
    title: { text: c.title, left: 'center' },
    tooltip: { trigger: 'item' },
    grid: { top: 60, bottom: 40, left: 70, right: 20 },
    xAxis: { type: 'value', name: c.x_axis?.label, nameLocation: 'center', nameGap: 28 },
    yAxis: { type: 'value', name: c.y_axis?.label, nameLocation: 'center', nameGap: 50 },
    legend: c.legend.length > 0 ? { data: c.legend, top: 28 } : undefined,
    series: [...scatterSeries, ...arrowSeries, ...ellipseSeries],
  }
}

/* ------------------------------------------------------------------ */
/*  Heatmap with cell value labels                                    */
/* ------------------------------------------------------------------ */

function heatmapOption(c: ChartContract): EChartsOption {
  const series = c.series[0]
  const xLabels = c.x_axis?.data as string[] ?? []
  const yLabels = c.y_axis?.data as string[] ?? []
  const range = (c.metadata?.value_range as [number, number]) ?? [-1, 1]

  return {
    title: { text: c.title, left: 'center' },
    tooltip: {
      trigger: 'item',
      formatter: (params: unknown) => {
        const p = params as { value: [number, number, number] }
        const v = p.value
        const xName = xLabels[v[0]] ?? ''
        const yName = yLabels[v[1]] ?? ''
        return `<b>${xName} - ${yName}</b><br/>r = ${v[2].toFixed(3)}`
      },
    },
    grid: { top: 60, bottom: 80, left: 80, right: 80 },
    xAxis: {
      type: 'category',
      data: xLabels,
      axisLabel: { rotate: 45 },
      name: c.x_axis?.label,
    },
    yAxis: {
      type: 'category',
      data: yLabels,
      name: c.y_axis?.label,
    },
    visualMap: {
      min: range[0],
      max: range[1],
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 5,
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#f7f7f7', '#fee090', '#fdae61', '#f46d43', '#a50026'],
      },
    },
    series: [
      {
        name: series.name,
        type: 'heatmap',
        data: series.data,
        label: {
          show: true,
          formatter: (params: unknown) => {
            const p = params as { value: [number, number, number] }
            return p.value[2].toFixed(2)
          },
          fontSize: 11,
          color: '#333',
        },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' },
        },
      },
    ],
  }
}

/* ------------------------------------------------------------------ */
/*  Regression Plot (coefficients display)                            */
/* ------------------------------------------------------------------ */

function regressionPlotOption(c: ChartContract): EChartsOption {
  const meta = c.metadata ?? {}
  const rSquared = meta.r_squared as number | undefined
  const equation = meta.equation as string | undefined
  const coefficients = meta.coefficients as Array<{
    term: string
    estimate: number
    std_error: number
    p_value: number | null
  }> | undefined

  if (!coefficients || coefficients.length === 0) {
    return fallbackOption(c)
  }

  const terms = coefficients.map((c) => c.term)
  const estimates = coefficients.map((c) => c.estimate)

  // Build subtitle with equation and R-squared
  const subtitleParts: string[] = []
  if (equation) subtitleParts.push(equation)
  if (rSquared != null) subtitleParts.push(`R\u00B2 = ${rSquared.toFixed(4)}`)

  return {
    title: {
      text: c.title || 'Linear Regression',
      subtext: subtitleParts.join('  |  '),
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
        const p = (Array.isArray(params) ? params[0] : params) as { name: string; value: number; dataIndex: number }
        const idx = p.dataIndex
        const coef = coefficients[idx]
        if (!coef) return ''
        const lines = [
          `<b>${coef.term}</b>`,
          `Estimate: ${coef.estimate.toFixed(4)}`,
          `Std. Error: ${coef.std_error.toFixed(4)}`,
        ]
        if (coef.p_value != null) lines.push(`p-value: ${coef.p_value.toFixed(4)}`)
        return lines.join('<br/>')
      },
    },
    grid: { top: 80, bottom: 40, left: 60, right: 20 },
    xAxis: { type: 'category', data: terms, axisLabel: { rotate: terms.length > 4 ? 30 : 0 } },
    yAxis: { type: 'value', name: 'Estimate' },
    series: [
      {
        name: 'Coefficients',
        type: 'bar',
        data: estimates,
        itemStyle: {
          color: (params: { dataIndex: number }) => {
            return estimates[params.dataIndex] >= 0 ? '#5470c6' : '#ee6666'
          },
        },
        barMaxWidth: 60,
      },
    ],
  }
}

/* ------------------------------------------------------------------ */
/*  Fallback                                                          */
/* ------------------------------------------------------------------ */

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
