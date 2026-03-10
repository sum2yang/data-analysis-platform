import { useRef, useCallback } from 'react'
import { Card, Empty } from 'antd'
import type { ECharts } from 'echarts'
import { GenericChart } from '@/components/GenericChart'
import { contractToEChartsOption } from '@/utils/chartTransform'
import type { ChartContract } from './types'

interface ChartPanelProps {
  contracts: ChartContract[]
  loading?: boolean
  onChartInstance?: (chart: ECharts) => void
}

export function ChartPanel({ contracts, loading = false, onChartInstance }: ChartPanelProps) {
  const chartRef = useRef<ECharts | null>(null)

  const handleReady = useCallback(
    (chart: ECharts) => {
      chartRef.current = chart
      onChartInstance?.(chart)
    },
    [onChartInstance],
  )

  if (contracts.length === 0 && !loading) {
    return (
      <Card>
        <Empty description="暂无图表，请先运行分析" />
      </Card>
    )
  }

  return (
    <div>
      {contracts.map((contract, i) => {
        const option = contractToEChartsOption(contract)
        return (
          <Card key={i} title={contract.title || `图表 ${i + 1}`} style={{ marginBottom: 16 }}>
            <GenericChart option={option} height={400} loading={loading} onChartReady={handleReady} />
          </Card>
        )
      })}
    </div>
  )
}
