import { describe, it, expect } from 'vitest'
import { contractToEChartsOption } from '@/utils/chartTransform'
import type { ChartContract } from '@/features/visualization/types'

describe('chartTransform', () => {
  const baseContract: Omit<ChartContract, 'chart_type' | 'series' | 'title'> = {
    x_axis: { label: 'X Axis', type: 'category', data: ['A', 'B', 'C'] },
    y_axis: { label: 'Y Axis', type: 'value' },
    annotations: [],
    legend: [],
    metadata: {},
  }

  it('transforms bar_error_letters correctly', () => {
    const contract: ChartContract = {
      ...baseContract,
      chart_type: 'bar_error_letters',
      title: 'Bar Chart',
      series: [
        {
          name: 'Series 1',
          type: 'bar',
          data: [10, 20, 30],
          error_bars: [1, 2, 3],
          color: '#ff0000',
        },
      ],
      annotations: [
        { type: 'letter', text: 'a', position: { x: 0.5, y: 35 } },
      ],
      legend: ['Series 1'],
    }

    const option = contractToEChartsOption(contract) as any
    expect(option.title.text).toBe('Bar Chart')
    expect(option.xAxis.data).toEqual(['A', 'B', 'C'])
    expect(option.series[0].type).toBe('bar')
    expect(option.series[0].data).toEqual([10, 20, 30])
    expect(option.series[0].itemStyle.color).toBe('#ff0000')
    expect(option.series[1].type).toBe('custom')
    // Letters now rendered via markPoint on the bar series
    expect(option.series[0].markPoint).toBeDefined()
    expect(option.series[0].markPoint.data).toHaveLength(1)
    expect(option.series[0].markPoint.data[0].value).toBe('a')
  })

  it('transforms bar_error_letters without error bars', () => {
    const contract: ChartContract = {
      ...baseContract,
      chart_type: 'bar_error_letters',
      title: 'Bar No Errors',
      series: [
        {
          name: 'Series 1',
          type: 'bar',
          data: [10, 20, 30],
        },
      ],
    }

    const option = contractToEChartsOption(contract) as any
    expect(option.series).toHaveLength(1)
    expect(option.series[0].type).toBe('bar')
  })

  it('transforms boxplot correctly', () => {
    const contract: ChartContract = {
      ...baseContract,
      chart_type: 'boxplot',
      title: 'Boxplot Chart',
      series: [
        {
          name: 'Box 1',
          type: 'boxplot',
          data: [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]],
        },
      ],
    }

    const option = contractToEChartsOption(contract) as any
    expect(option.series[0].type).toBe('boxplot')
    expect(option.series[0].data).toEqual([[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]])
  })

  it('transforms violin to boxplot format correctly', () => {
    const contract: ChartContract = {
      ...baseContract,
      chart_type: 'violin',
      title: 'Violin Chart',
      series: [
        {
          name: 'Violin 1',
          type: 'violin',
          data: [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]],
        },
      ],
    }

    const option = contractToEChartsOption(contract) as any
    // Violin now renders as boxplot + jitter scatter (2 series)
    expect(option.series[0].type).toBe('boxplot')
    const stats = option.series[0].data[0]
    expect(stats).toHaveLength(5)
    expect(stats[0]).toBe(1)
    expect(stats[4]).toBe(10)
    expect(option.series[1].type).toBe('scatter')
  })

  it('handles violin with empty data array', () => {
    const contract: ChartContract = {
      ...baseContract,
      chart_type: 'violin',
      title: 'Violin Empty',
      series: [{ name: 'V', type: 'violin', data: [[]] }],
    }

    const option = contractToEChartsOption(contract) as any
    expect(option.series[0].data[0]).toEqual([0, 0, 0, 0, 0])
    // Scatter jitter series exists but has no data points for empty input
    expect(option.series[1].type).toBe('scatter')
  })

  it('transforms scatter correctly with multiple series', () => {
    const contract: ChartContract = {
      ...baseContract,
      chart_type: 'scatter',
      title: 'Scatter Chart',
      series: [
        { name: 'S1', type: 'scatter', data: [[1, 2], [2, 3]] },
        { name: 'S2', type: 'scatter', data: [[3, 4], [4, 5]] },
      ],
      legend: ['S1', 'S2'],
    }

    const option = contractToEChartsOption(contract) as any
    expect(option.series).toHaveLength(2)
    expect(option.series[0].type).toBe('scatter')
    expect(option.series[1].type).toBe('scatter')
    expect(option.legend.data).toEqual(['S1', 'S2'])
    expect(option.xAxis.type).toBe('value')
    expect(option.yAxis.type).toBe('value')
  })

  it('transforms heatmap correctly', () => {
    const contract: ChartContract = {
      ...baseContract,
      chart_type: 'heatmap',
      title: 'Heatmap',
      x_axis: { type: 'category', data: ['X1', 'X2'], label: 'X' },
      y_axis: { type: 'category', data: ['Y1', 'Y2'], label: 'Y' },
      series: [{ name: 'Heat', type: 'bar', data: [[0, 0, 0.5], [1, 1, 0.8]] }],
    }

    const option = contractToEChartsOption(contract) as any
    expect(option.series[0].type).toBe('heatmap')
    expect(option.visualMap).toBeDefined()
    expect(option.visualMap.min).toBe(-1)
    expect(option.visualMap.max).toBe(1)
    expect(option.xAxis.data).toEqual(['X1', 'X2'])
  })

  it('uses fallback for unknown chart types', () => {
    const contract = {
      chart_type: 'unknown' as any,
      title: 'Fallback',
      series: [{ name: 'Default', type: 'bar', data: [1, 2, 3] }],
      x_axis: { data: ['A', 'B', 'C'] },
      annotations: [],
      legend: [],
      metadata: {},
    } as ChartContract

    const option = contractToEChartsOption(contract) as any
    expect(option.title.text).toBe('Fallback')
    expect(option.series[0].type).toBe('bar')
  })

  it('handles empty series data', () => {
    const contract: ChartContract = {
      chart_type: 'bar_error_letters',
      title: 'Empty',
      series: [{ name: 'S', type: 'bar', data: [] }],
      annotations: [],
      legend: [],
      metadata: {},
    }

    const option = contractToEChartsOption(contract) as any
    expect(option.xAxis.data).toEqual([])
    expect(option.series[0].data).toEqual([])
  })
})
